class LevenshteinAutomaton:
    def __init__(self, string, n):
        self.string = string
        self.max_edits = n
    def start(self):
        return range(len(self.string)+1)

    def step(self, state, c):
        new_state = [state[0]+1]
        for i in range(len(state)-1):
            cost = 0 if self.string[i] == c else 1
            new_state.append(min(new_state[i]+1, state[i]+cost, state[i+1]+1))
        return new_state

    def is_match(self, state):
        return state[-1] <= self.max_edits

    def can_match(self, state):
        return min(state) <= self.max_edits

def test(string, n):
    la = LevenshteinAutomaton(string,n)
    words = ["wrong","banana"]
    for word in words:
        state = la.start()
        counter = 0
        for char in word:
            counter += 1
            state = la.step(state, char)
            if not la.can_match(state):
                print "%s not match!" % word
                break
            if counter == len(word):
                print "%s matched!" % word

test("bannana",2)
