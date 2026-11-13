#!/usr/bin/env python3
"""Draw the three README figures in VectorCraft: hero, turn-flow and parts.

VectorCraft does the drawing; this script only sends it commands over its local control
server. Start an instance with the control server on and an automation root that holds
--out, for example:

    VectorCraft --control 7991 --automation-read-root OUT --automation-write-root OUT

The gate names come from hooks/hooks.json and the skill names from skills/*/, so a figure
redrawn after a change says what the repo says. The banner in the hero leaves out the version
number on purpose: a picture cannot follow releases, and a stale number misleads.
Words, colours and fonts are in figures.json next to this file. Each figure is written to
--out as <name>.vectorcraft (the editable original), .svg (text as outlines), .pdf and .png.
"""

import argparse
import json
import os
import socket
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
WIDTH = 1200                  # pt; README images are shown at most about this wide
CARD_RADIUS = 16
PNG_SCALE_DEFAULT = 3         # pixels per point: 3600 px wide, sharp on high-density screens
CAP_HEIGHT = 0.36             # Inter's capitals are about 0.72 em tall: a baseline this far below a centre line centres them
SCRATCH_PAGE_HEIGHT = 1000    # pt; drawn on this, then the artboard is cut to the card's height


class VectorCraft:
    """One open connection to a VectorCraft control server."""

    def __init__(self, port, timeout):
        self.sock = socket.create_connection(("127.0.0.1", port), timeout)
        self.sock.settimeout(timeout)
        self.stream = self.sock.makefile("rwb")
        self.request_id = 0

    def run(self, command, **params):
        """Run one engine command and return what it made; an error stops the drawing."""
        self.request_id += 1
        request = {"id": self.request_id, "method": "engine.execute",
                   "params": {"command": command, "params": params}}
        self.stream.write((json.dumps(request) + "\n").encode())
        self.stream.flush()
        reply = json.loads(self.stream.readline())
        if not reply.get("ok"):
            raise RuntimeError("%s failed: %s" % (command, reply.get("error")))
        made = reply.get("result") or {}
        if isinstance(made, dict) and made.get("warning"):
            print("warning (%s): %s" % (command, made["warning"]), file=sys.stderr)
        return made


class Canvas:
    """Drawing calls with the house colours and fonts; every call returns the object id."""

    def __init__(self, app, style):
        self.app = app
        self.color = style["colors"]
        self.sans = style["fonts"]["sans"]
        self.mono = style["fonts"]["mono"]

    def paint(self, object_id, fill=None, stroke=None, weight=1.0, dash=None):
        """Set an object's fill and stroke; None means no paint."""
        self.app.run("paint.setFill", ids=[object_id], **({"color": fill} if fill else {"none": True}))
        self.app.run("paint.setStroke", ids=[object_id], **({"color": stroke} if stroke else {"none": True}))
        if stroke:
            self.app.run("stroke.set", ids=[object_id], weight=weight, dash=dash)

    def rect(self, left, top, width, height, fill=None, stroke=None, weight=1.0, radius=0):
        object_id = self.app.run("shape.rectangle", x=left, y=top, width=width, height=height, radius=radius)["id"]
        self.paint(object_id, fill, stroke, weight)
        return object_id

    def circle(self, centre_x, centre_y, diameter, fill=None, stroke=None, weight=1.0):
        object_id = self.app.run("shape.ellipse", x=centre_x - diameter / 2, y=centre_y - diameter / 2,
                                 width=diameter, height=diameter)["id"]
        self.paint(object_id, fill, stroke, weight)
        return object_id

    def line(self, points, color, weight=1.5, dash=None, end_arrow=None):
        """An open path through the points, round caps, with an arrowhead at the end if asked."""
        anchors = [{"x": point_x, "y": point_y} for point_x, point_y in points]
        object_id = self.app.run("path.create", anchors=anchors, closed=False)["id"]
        self.paint(object_id, None, color, weight, dash)
        stroke_style = {"cap": "round", "join": "round"}
        if end_arrow:
            stroke_style.update(endArrow=end_arrow, arrowAlign="tip")
        self.app.run("stroke.set", ids=[object_id], **stroke_style)
        return object_id

    def text(self, left, baseline, words, size, color, mono=False, style="Regular", justify="left", tracking=None):
        """Point type: one line, its baseline at `baseline` (with justify=center, `left` is the centre)."""
        made = self.app.run("text.create", x=left, y=baseline, text=words, size=size,
                            font=self.mono if mono else self.sans, style="Regular" if mono else style,
                            color=color, justify=justify)
        if tracking:
            self.app.run("text.setStyle", ids=[made["id"]], tracking=tracking)
        return made["id"]

    def paragraph(self, left, top, width, words, size, color):
        """Area type that wraps inside `width` and grows downward as it needs."""
        made = self.app.run("text.create", x=left, y=top, text=words, size=size, font=self.sans,
                            style="Regular", color=color, area={"width": width, "height": size * 4, "fit": "autoHeight"})
        return made["id"]

    def centred_text(self, centre_x, centre_y, words, size, color, **options):
        """Text whose capitals are centred on (centre_x, centre_y)."""
        return self.text(centre_x, centre_y + size * CAP_HEIGHT, words, size, color, justify="center", **options)

    def group(self, ids, name):
        group_id = self.app.run("object.group", ids=ids)["id"]
        self.app.run("object.setProps", id=group_id, name=name)
        return group_id

    def card(self, height):
        """The white rounded card every figure sits on; outside it the PNG is transparent."""
        return self.rect(0.5, 0.5, WIDTH - 1, height - 1, self.color["card"], self.color["border"], 1, CARD_RADIUS)


def repo_facts():
    """Gate names by hook event and skill names, read from the repo."""
    with open(os.path.join(REPO, "hooks", "hooks.json"), encoding="utf-8") as handle:
        hooks = json.load(handle)["hooks"]
    gates = {}
    for event, groups in hooks.items():
        for group in groups:
            names = [hook["command"].split()[-1] for hook in group["hooks"]]
            gates[(event, group.get("matcher"))] = names
    skills = sorted(name for name in os.listdir(os.path.join(REPO, "skills"))
                    if os.path.isfile(os.path.join(REPO, "skills", name, "SKILL.md")))
    return gates, skills


def stage_gates(gates, stage):
    """The gates of one stage: its event, and its matcher when the event has several groups."""
    if "matcher" in stage:
        return gates.get((stage["event"], stage["matcher"]), [])
    return [name for (event, _), names in gates.items() if event == stage["event"] for name in names]


def gate_count(gates):
    """Gates the banner counts: all but the one that prints the banner."""
    return sum(len(names) for (event, _), names in gates.items() if event != "SessionStart")


def draw_hero(canvas, words, gates, skills):
    """Name, one-line pitch and three counts on the left; the real install commands and banner on the right."""
    colors, height = canvas.color, 412
    ids = [canvas.card(height)]
    left = 64
    ids.append(canvas.text(left, 100, words["eyebrow"], 13, colors["accent"], mono=True, tracking=120))
    ids.append(canvas.text(left, 190, words["title"], 88, colors["ink"], style="SemiBold", tracking=-30))
    ids.append(canvas.paragraph(left, 212, 470, words["subtitle"], 21, colors["muted"]))
    stats = [(len(skills), "skills"), (gate_count(gates), "hook gates"), (words["languages"], "languages")]
    for index, (number, label) in enumerate(stats):
        stat_left = left + index * 132
        ids.append(canvas.text(stat_left, 336, str(number), 30, colors["ink"], style="SemiBold"))
        ids.append(canvas.text(stat_left, 360, label, 14, colors["muted"]))
        if index:
            ids.append(canvas.line([(stat_left - 20, 310), (stat_left - 20, 364)], colors["rule"], 1))
    canvas.group(ids, "hero text")

    term_left, term_width, term_height = 604, 532, 250
    term_top = (height - term_height) / 2
    term = [canvas.rect(term_left, term_top, term_width, term_height, colors["terminal"], None, 0, 12)]
    term.append(canvas.rect(term_left, term_top, term_width, 36, colors["terminal_bar"], None, 0, 12))
    term.append(canvas.rect(term_left, term_top + 24, term_width, 12, colors["terminal_bar"]))  # squares the bar's lower corners
    for index, dot in enumerate(colors["dots"]):
        term.append(canvas.circle(term_left + 22 + index * 20, term_top + 18, 12, dot))
    term.append(canvas.centred_text(term_left + term_width / 2, term_top + 18, words["terminal_title"], 12,
                                    colors["terminal_dim"], mono=True))
    baseline = term_top + 80
    for command in words["commands"]:
        term.append(canvas.text(term_left + 28, baseline, ">", 15, colors["terminal_prompt"], mono=True))
        term.append(canvas.text(term_left + 50, baseline, command, 15, colors["terminal_ink"], mono=True))
        baseline += 32
    term.append(canvas.text(term_left + 28, baseline + 26, words["restart"], 14, colors["terminal_dim"], mono=True))
    # 버전 번호는 넣지 않는다: 그림은 배포를 따라가지 못해서, 다음 배포부터 틀린 번호가 된다(2026-11-13)
    banner = "KL-SKILLS GATES — loaded, %d rules enforced" % gate_count(gates)
    term.append(canvas.text(term_left + 28, baseline + 60, banner, 14, colors["terminal_banner"], mono=True))
    canvas.group(term, "terminal")
    return height


def draw_turn_flow(canvas, words, gates):
    """Five numbered moments on a time axis, each with its gates stacked underneath as chips."""
    colors = canvas.color
    stages = words["stages"]
    columns = [stage_gates(gates, stage) for stage in stages]
    chip_height, chip_gap, chip_width = 30, 10, 192
    chips_top = 252
    tallest = max(len(names) for names in columns)
    legend_baseline = chips_top + tallest * (chip_height + chip_gap) + 30
    height = legend_baseline + 44
    ids = [canvas.card(height)]
    ids.append(canvas.text(48, 60, words["title"], 22, colors["ink"], style="SemiBold"))
    ids.append(canvas.text(48, 88, words["subtitle"], 15, colors["muted"]))
    canvas.group(ids, "title")

    # 단계 사이 간격을 같게: 양 끝 단계의 중심은 카드 가장자리에서 120pt 안쪽
    step = (WIDTH - 2 * 120) / (len(stages) - 1)
    column_centres = [120 + index * step for index in range(len(stages))]
    axis_y = 150
    canvas.line([(column_centres[0] - 56, axis_y), (column_centres[-1] + 64, axis_y)], colors["rule"], 2,
                end_arrow="Triangle")
    for index, (stage, names) in enumerate(zip(stages, columns)):
        centre = column_centres[index]
        part = [canvas.circle(centre, axis_y, 34, colors["card"], colors["accent"], 2)]
        part.append(canvas.centred_text(centre, axis_y, str(index + 1), 14, colors["accent"], style="SemiBold"))
        part.append(canvas.centred_text(centre, 196, stage["label"], 16, colors["ink"], style="SemiBold"))
        part.append(canvas.centred_text(centre, 220, stage["detail"], 12, colors["faint"], mono=True))
        for row, name in enumerate(names):
            top = chips_top + row * (chip_height + chip_gap)
            sends_back = name in words["sends_back"]   # 답을 돌려보낼 수 있는 게이트는 주황으로
            part.append(canvas.rect(centre - chip_width / 2, top, chip_width, chip_height,
                                    colors["back_soft"] if sends_back else colors["surface"],
                                    colors["back_border"] if sends_back else colors["rule"], 1, 8))
            part.append(canvas.centred_text(centre, top + chip_height / 2, name, 14,
                                            colors["back_ink"] if sends_back else colors["ink"], mono=True))
        canvas.group(part, "stage %d %s" % (index + 1, stage["label"]))

    legend = [canvas.rect(48, legend_baseline - 14, 18, 18, colors["surface"], colors["rule"], 1, 5),
              canvas.text(76, legend_baseline, words["legend_gate"], 14, colors["muted"]),
              canvas.rect(196, legend_baseline - 14, 18, 18, colors["back_soft"], colors["back_border"], 1, 5),
              canvas.text(224, legend_baseline, words["legend_back"], 14, colors["muted"])]
    canvas.group(legend, "legend")
    return height


def draw_parts(canvas, words, gates, skills):
    """Message → Claude Code → three cards (skills, hook gates, wiki), joined by labelled elbows."""
    colors, height = canvas.color, 500
    ids = [canvas.card(height)]
    ids.append(canvas.text(48, 60, words["title"], 22, colors["ink"], style="SemiBold"))
    ids.append(canvas.text(48, 88, words["subtitle"], 15, colors["muted"]))
    canvas.group(ids, "title")

    # 왼쪽: 메시지 → Claude Code
    mid_y = 296
    message_width = 236
    message = [canvas.rect(48, mid_y - 40, message_width, 80, colors["card"], colors["border"], 1, 12),
               canvas.text(76, mid_y - 4, words["message"], 17, colors["ink"], style="SemiBold"),
               canvas.text(76, mid_y + 20, words["message_detail"], 13, colors["muted"], mono=True)]
    canvas.group(message, "message")
    hub_left, hub_width, hub_height = 380, 236, 112
    hub = [canvas.rect(hub_left, mid_y - hub_height / 2, hub_width, hub_height, colors["ink"], None, 0, 14),
           canvas.centred_text(hub_left + hub_width / 2, mid_y - 12, words["center"], 21, colors["card"], style="SemiBold"),
           canvas.centred_text(hub_left + hub_width / 2, mid_y + 20, words["center_detail"], 13, colors["faint"], mono=True)]
    canvas.group(hub, "claude code")
    canvas.line([(48 + message_width, mid_y), (hub_left - 4, mid_y)], colors["accent"], 2, end_arrow="Triangle")

    # 오른쪽: 세 카드. 개수는 저장소에서 센 값, 위키는 개수 대신 배지 글자
    counts = {"skills": str(len(skills)), "gates": str(gate_count(gates))}
    tints = {"skills": (colors["accent_soft"], colors["accent"]), "gates": (colors["gate_soft"], colors["gate"]),
             "wiki": (colors["wiki_soft"], colors["wiki"])}
    card_left, card_width, card_height, card_gap = 808, 344, 104, 22
    first_top = mid_y - (3 * card_height + 2 * card_gap) / 2
    branch_x = 664          # 마지막 가로선이 길어야 "writes · recalls" 라벨이 카드에 안 가린다
    for index, card in enumerate(words["parts_cards"]):
        top = first_top + index * (card_height + card_gap)
        card_mid = top + card_height / 2
        soft, strong = tints[card["kind"]]
        part = [canvas.line([(hub_left + hub_width, mid_y), (branch_x, mid_y), (branch_x, card_mid), (card_left, card_mid)],
                            colors["rule"], 1.5)]
        part.append(canvas.text(branch_x + 10, card_mid - 8, card["link"], 13, colors["muted"], mono=True))
        part.append(canvas.rect(card_left, top, card_width, card_height, colors["card"], colors["border"], 1, 12))
        part.append(canvas.circle(card_left, card_mid, 7, colors["card"], colors["faint"], 1.5))   # 카드 테두리 위에
        part.append(canvas.rect(card_left + 20, top + 22, 44, 44, soft, None, 0, 10))
        badge = counts.get(card["kind"], card.get("badge", ""))
        part.append(canvas.centred_text(card_left + 42, top + 44, badge, 17, strong, style="SemiBold"))
        part.append(canvas.text(card_left + 80, top + 36, card["title"], 17, colors["ink"], style="SemiBold"))
        part.append(canvas.text(card_left + 80, top + 58, card["detail"], 14, colors["muted"]))
        footnote = card.get("path") or " · ".join(card["examples"]) + " …"
        part.append(canvas.text(card_left + 80, top + 82, footnote, 12, colors["faint"], mono=True))
        canvas.group(part, card["kind"])
    return height


def save(app, out_dir, name, png_scale):
    """Save the editable original and export SVG, PDF and PNG next to it."""
    stem = os.path.join(out_dir, name)
    app.run("file.saveAs", path=stem + ".vectorcraft")
    app.run("document.export", path=stem + ".svg", format="svg", svg={"outlineText": True})
    app.run("document.export", path=stem + ".pdf", format="pdf")
    app.run("document.export", path=stem + ".png", format="png", scale=png_scale, background="transparent")
    app.run("file.close")
    return [stem + ext for ext in (".vectorcraft", ".svg", ".pdf", ".png")]


def main():
    """Draw the figures asked for, one document each, and print the files written."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--port", type=int, required=True, help="VectorCraft control port")
    parser.add_argument("--out", required=True, help="folder inside the instance's automation write root")
    parser.add_argument("--only", choices=["hero", "turn-flow", "parts"], action="append",
                        help="draw only these figures (repeatable); default all three")
    parser.add_argument("--png-scale", type=float, default=PNG_SCALE_DEFAULT, help="PNG pixels per point")
    parser.add_argument("--timeout", type=float, default=55)
    args = parser.parse_args()

    with open(os.path.join(HERE, "figures.json"), encoding="utf-8") as handle:
        style = json.load(handle)
    style["parts"]["parts_cards"] = style["parts"].pop("cards")
    gates, skills = repo_facts()
    out_dir = os.path.abspath(args.out)
    app = VectorCraft(args.port, args.timeout)
    figures = {
        "hero": lambda canvas: draw_hero(canvas, style["hero"], gates, skills),
        "turn-flow": lambda canvas: draw_turn_flow(canvas, style["turn_flow"], gates),
        "parts": lambda canvas: draw_parts(canvas, style["parts"], gates, skills),
    }
    for name in args.only or list(figures):
        # 높이는 배치가 끝나야 알 수 있다: 긴 쪽지에 그린 뒤 아트보드를 카드 높이로 자른다
        app.run("file.new", name=name, width=WIDTH, height=SCRATCH_PAGE_HEIGHT, units="Points",
                backgroundContents="transparent")
        height = figures[name](Canvas(app, style))
        app.run("artboard.setProps", index=0, x=0, y=0, width=WIDTH, height=height, moveArt=False)
        for path in save(app, out_dir, name, args.png_scale):
            print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
