from multiprocessing import Process, Value
import time


class myCl():
    def __init__(self):
        self.a = 0
        self.b = 0
        self.y = True

    def count_plus(self, check=False, fuck=''):
        print(f'In plus: {fuck.value}')
        while(1):
            time.sleep(0.1)
            self.a += 1
            print(f'In plus: {self.a}')
            if(self.a == 5):
                check.value = False
                break

    def count_min(self, check, val):
        print(f'In min: {val.value}')
        val.value = 5
        while(check.value):
            time.sleep(2)
            self.a -= 1
            print(f'In minus: {self.a}')

    def call(self):
        check = Value('i', True)
        val = Value('i', 123456)

        infinit_process = Process(target=self.count_min, args=[check, val])
        control_process = Process(target=self.count_plus, args=[check, val])

        infinit_process.start()
        control_process.start()

        # alles läuft aber er wartet an join() save bis fertig.
        print('start done')
        control_process.join()
        print(self.a)
        infinit_process.join()
        print('join done')
        print(self.a)


if(__name__ == '__main__'):

    i = myCl()
    i.call()

# _____________________________________________________________ second example
# def count_plus(y=False):
#     print(f'y in plus: {y.value}')

#     for i in range(5):
#         time.sleep(1)
#         print(f'plus {i}')
#     y.value = False
#     print(f'y in plus 2nd: {y.value}')


# def count_min(y=False):
#     print(f'y in min: {y.value}')

#     while(y.value):
#         print(f'In while {y.value}')
#         time.sleep(1)


# def call():
#     y = Value('i', True)
#     p1 = Process(target=count_plus, args=[y])
#     p2 = Process(target=count_min, args=[y])
#     p1.start()
#     p2.start()
#     p1.join()
#     p2.join()


# if(__name__ == '__main__'):
#     call()
