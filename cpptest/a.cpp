#include "a.h"
#include <iostream>

using namespace std;

Hello::Hello(){
    cout << "Some one create me!" << endl;
}

Hello::~Hello(){
    cout << "Some one delete me!" << endl;
}
#define TEST(str) \
    cout << str << endl;
void Hello::say(){
    TEST("I am LC");
}

int main(){
    {
        Hello hello;
        hello.say();
    }
}
