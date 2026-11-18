// expect: vague-name:q vague-name:tmp no-docstring:total

#include <vector>

/// 수를 모은다.
class Bag {
public:
    int total() const;
private:
    std::vector<int> items_;
};

int Bag::total() const {
    int q = 0;
    auto tmp = q;
    for (int item : items_) {
        tmp += item;
    }
    return tmp;
}
