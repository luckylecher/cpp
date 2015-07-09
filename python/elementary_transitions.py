class Position:
    def __init__(self,i,e):
        self.i = i
        self.e = e
        
    def setWordLen(self,w):
        self.w = w

    def toString(self):
        print "%d # %d" % (self.i,self.e)

    def reset(self,i,e):
        self.i = i
        self.e = e
        
class Caculate:
    def __init__(self):
        self.v=[]
        self.word = ""
        self.x = ''
        self.position = Position(0,0)
        self.n = 2

    def setN(self,n):
        self.n = n
        
    def setWord(self,word):
        self.word = word
        self.w = len(word)

    def setX(self,x):
        self.x = x

    def test(self,word,x):
        self.setWord(word)
        self.setX(x)
        
    def caculateVector(self):
        self.v=[]
        counter = 0
        for char in self.word:
            counter += 1
            if counter <= self.position.i:
                continue
            if char == self.x:
                self.v.append(1)
            else:
                self.v.append(0)
        print self.v

    def printVector(self):
        print self.v

    def nextPosition(self):
        self.caculateVector()
        self.next = []
        if self.position.e <= self.n - 1:
            if self.position.i <= self.w - 2:
                self._fun_1()
            elif self.position.i == self.w - 1:
                self._fun_2()
            else:
                self._fun_3()
        elif self.position.e == self.n:
            if self.position.i <= self.w - 1:
                self._fun_4()
            elif self.position.i == self.w:
                self._fun_5()
        self.showNext()

    def _find_first_one(self):
        i = 1
        for item in self.v:
            if item == 1:
                return i
            i += 1
            

    def _fun_1(self):
        first_1 = self._find_first_one()
        if first_1 == 1:
            # x is right char ,no need to change
            self.next.append(Position(self.position.i + 1, self.position.e))
        elif first_1 <= len(self.v):
            # x is wrong char , just delete it
            self.next.append(Position(self.position.i, self.position.e + 1))
            # replace x with a correct char
            self.next.append(Position(self.position.i + 1, self.position.e + 1))
            # fill correct char until meet x, take j-1 operates
            self.next.append(Position(self.position.i + first_1,
                                      self.position.e + first_1 -1))
        else:
            # just delete x
            self.next.append(Position(self.position.i, self.position.e + 1))
            # replace x with a correct char
            self.next.append(Position(self.position.i + 1, self.position.e + 1))
            
    def _fun_2(self):
        first_1 = self._find_first_one()
        if first_1 == 1:
            #/**x is right char ,no need to other operate**/
            self.next.appen(Position(self.position.i + 1, self.position.e))
        else:
            #/**delete x**/
            self.next.append(Position(self.position.i, self.position.e + 1))
            #/**replace x with right char**/
            self.next.append(Position(self.position.i + 1, self.position.e + 1))


    def _fun_3(self):
        #/**just replace x with right char**/
        self.next.append(Position(self.position.i, self.position.e + 1))

    def _fun_4(self):
        first_1 = self._find_first_one()
        if first_1 == 1:
            # x is right char ,no need other operate
            self.next.append(Position(self.position.i + 1, self.n))
        else:
            # failed
            self.next.append(None)
    
    def _fun_5(self):
        self.next.append(None)
            
    def showNext(self):
        print "------NEXT-----"
        for item in self.next:
            if item is None:
                print "None"
            else:
                item.toString()

clt = Caculate()
clt.test("cbabcdcc","c")
clt.setN(5)
clt.position.reset(2,0)
clt.nextPosition()

