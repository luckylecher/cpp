#include <pthread.h>
#include <iostream>
#include <string>

int g_Flag = 0;
typedef void *(*func)(void *);

struct Msg {
    std::string info;
};

void* thread1(void *);

int main(int argc, char** argv)
{
    std::cout << "main thread" << std::endl;
    pthread_t tid_1, tid_2;
    Msg msg_1;
    msg_1.info = "I am thread 1.";
    std::cout << msg_1.info << std::endl;
    pthread_create(&tid_1, NULL, thread1, NULL);
    return 0;
}

void *thread1(void *v_msg) {
    std::cout << "thread has been created" << std::endl;
    Msg *msg = static_cast<Msg *> (v_msg);
    std::cout << msg->info << std::endl;
    pthread_exit(0);
}
