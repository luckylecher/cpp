#include<iostream>
using namespace std;

enum {
    E_H=9,
};

enum {
    E_H_1,
};

int main(){
    int z = E_H;
    cout<<E_H << "," <<E_H_1<<endl;
    if(E_H == E_H_1)
        cout<<"yes"<<endl;
}
