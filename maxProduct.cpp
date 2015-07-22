#include<iostream>
#include<vector>
using namespace std;
class Solution{
public:
    int deal(vector<int> &num);
    int max(int a, int b);
    int min(int a, int b);  
};

int Solution::deal(vector<int> &num){
    vector <int>::iterator itr = num.begin();
    int cur_max, cur_min, real_max, temp;
    cur_max = cur_min = real_max = *itr;
    itr++;
    while( itr != num.end() ){
        temp = cur_max;
        if(*itr > 0){
            cur_max = max( (*itr) * cur_max, *itr);
            cur_min = min( *itr, (*itr) * cur_min);
        }else if(*itr < 0){
            cur_max = max( (*itr) * cur_min, *itr);
            cur_min = min( (*itr) * temp, *itr);
        }else{
            cur_min = cur_max = *itr;
        }
        cout << cur_max << "," << cur_min << endl;
        real_max = max(cur_max, real_max);
        itr++;
    }
    return real_max;
}

int Solution::max(int a, int b){
    return a > b ? a : b;
}

int Solution::min(int a, int b){
    return a > b ? b : a;
}

int main(){
    Solution so;
    vector<int> v;
    v.push_back(-4);
    v.push_back(-3);
    v.push_back(-2);
    cout << so.deal(v) << endl;
}
