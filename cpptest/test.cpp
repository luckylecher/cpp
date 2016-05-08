#include <iostream>
#include <map>
#include <vector>
#include <string>
#include <stdlib.h>
#include <sstream>
using namespace std;

struct st1{
    int b;
    char a[9];
    int64_t c;
};
struct st2{
    char a;
    double c;
    short b;
};

class TestVirtualDestructorBase{
public:
    TestVirtualDestructorBase(){ cout << "Papa is here." << endl;}
    virtual ~TestVirtualDestructorBase(){ cout << "Papa has gone." << endl;}
};

class TestVirtualDestructorChild : public TestVirtualDestructorBase{
public:
    TestVirtualDestructorChild() { cout << "Son is here." << endl;}
    ~TestVirtualDestructorChild() { cout << "Son has gone." << endl;}
};

class TestMap {
public:
    map<string, string> _map;
    void beginTest() {
        _map["gril"] = "hongqing";
        _map["but"] = "word";
        _map["boy"] = "lijian";
        _map["and"] = "conjunction";
        printMap(_map);
    }
    template <class T>
    void printMap(map<string, T> &sheep) {
        for (map<string, string>::const_iterator it = sheep.begin(); it != sheep.end(); it++) {
            cout << it->first << endl;
        }
    }
};

class TestChar {
public:
    void beginTest() {
        std::string str="a苹果b<";
        for (int i=0; i < str.size(); i++) {
            if (str[i] < 0) {
                std::cout << "This char is nagetive." << std::endl;
            } else {
                std::cout << "This char is positive" << std::endl;
            }
        }
    }
};

class TestVector {
public:
    void beginTest() {
        vector<int> a;
        vector<int> b(3,1);
        b.insert(b.begin(), a.begin(), a.end());
        printVector(b);    
    }
    void printVector(vector<int> &vec){
        for (vector<int>::const_iterator it = vec.begin(); it != vec.end(); it++){
            cout << *it <<"\t";
        }
        cout<<endl;
    }
};

class TestUnicode {
public:
    void beginTest(){
        std::string str("中国");
        const char *a = str.c_str();
        for (int i=0;a[i]!='\0';i++) {
            ;
        }
    }
};

class TestArray {
public:
    void beginTest(){
        std::string sary[] = {"a", "b", "c"};
        size_t size = sizeof(sary) / sizeof(std::string);
        std::cout<<size<<std::endl;
    }
};

class TestSizeT{
public:
    void beginTest(size_t x){
        int y = 100;
        char z = 'a';
        std::cout << (x == z ? "Equal" : "Not Equal") << std::endl;
        std::cout << (int(x) == z ? "Equal" : "Not Equal") << std::endl;
    }
};

class TestUnicode2UTF8 {
public:
    unsigned long transformUnicodeString(const std::string &str) {//"4A8F"
        if (str.size() != 4) {
            return 0;
        }
        unsigned long ret = 0;
        for (size_t i = 0; i < 4; ++i) {
            std::cout << char2int(str[i]) << std::endl;
            ret += char2int(str[i]) + ret * 16;
        }
        return ret;
    }
    unsigned int char2int(char ch) {
        switch(ch){
            case '0':
            case '1':
            case '2':
            case '3':
            case '4':
            case '5':
            case '6':
            case '7':
            case '8':
            case '9':
                return ch - '0';
                break;
            case 'A':
            case 'a':
                return 10;
            case 'B':
            case 'b':
                return 11;
            case 'C':
            case 'c':
                return 12;
            case 'D':
            case 'd':
                return 13;
            case 'E':
            case 'e':
                return 14;
            case 'F':
            case 'f':
                return 15;
            default:
                return 0;
        }
    }
};

int main(){
    {
        TestVirtualDestructorBase *t1 = new TestVirtualDestructorChild();
        delete t1;
    }
    TestUnicode2UTF8 test1;
    std::cout << test1.transformUnicodeString("2A3b") << std::endl;
    TestArray ta;
    ta.beginTest();
    TestSizeT test2;
    size_t i = 97;
    test2.beginTest(i);
}
