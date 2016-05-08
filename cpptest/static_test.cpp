#include "static_test.h"

const std::string A::str = A::init();

A::A(){}
A::~A(){}
std::string A::init(){
    std::cout << "hello" << std::endl;
    return std::string("111");
}
