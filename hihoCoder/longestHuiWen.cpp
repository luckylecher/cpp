#include<iostream>
#include<vector>
#include<string>
using namespace std;
class Solution{
private:
    vector<string> rawData;
public:
    void read_data();
    void print_data();
    int deal_string(string &str);
    int deal_huiwen(string &str,int center);
};
void Solution::read_data(){
    int stringNumber;
    cin >> stringNumber;
    for(int i=0; i < stringNumber; i++){
        string tempStr;
        cin >> tempStr;
        cout << deal_string(tempStr) << endl;
    }
}
void Solution::print_data(){
    for(int i = 0; i < rawData.size(); i++){
        cout << rawData[i] << endl;
    }
}
int Solution::deal_string(string &str){
    int size = str.size(),max=0;
    for(int i = 0; i < size; i++){
        int temp = deal_huiwen(str, i);
        max = max > temp ? max : temp;
    }
    return max;
}
int Solution::deal_huiwen(string &str,int center){
    int size = str.size();
    int head=center;
    int tail=center;
    int max=0,count=0;
    while(head > -1 && tail < size && str[head--] == str[tail++]){
        count++;
    }
    max = 2 * count -1;
    count = 0;
    head=center,tail=center+1;
    while(head > -1 && tail < size && str[head--] == str[tail++]){
        count++;
    }
    count = 2 * count;
    return max > count ? max : count;
}
int main(){
    Solution solution;
    solution.read_data();
    solution.print_data();
    
}
