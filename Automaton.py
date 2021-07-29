from Grid import Grid

#This function converts a decimal integer into another base
#Can only convert to bases 10 or below
def decToBase(x, base):
    if x >= base:
        return decToBase(x//base, base) + str(x%base)
    else:
        return str(x%base)

#This function pads a number represented as a string with zeroes to reach the requested length
#Used to ensure automata generated from an integer have the same number of digits as neighbourhoods
#Also used to fill initial conditions to reach the correct length in generate_ics
def padNumber(x, length):
    return "0" * (length-len(x)) + x

#Class to represent an automaton
class Automaton:
    def __init__(self, k, r, code, initial_conditions, max_steps):
        #k is number of states, r is radius of neighbourhood
        self.k = k
        self.r = r
        neighbourhood_size = 2*r+1
        num_neighbourhoods = k ** neighbourhood_size
        #Use k and r to produce each unique neighbourhood. These are created counting down, to match the order used by Rule notation of elementary automata
        neighbourhoods = [padNumber(decToBase(x, k), neighbourhood_size) for x in range(num_neighbourhoods-1,-1,-1)]
        #Convert the decimal integer code into a base k representation
        code = list(padNumber(str(decToBase(code, k)), num_neighbourhoods))
        #read off the states and assign each the subsequent digit. The pop method removes the first item, so we can just iterate over the neighbourhoods 
        self.next_cell = {}
        for value_in in neighbourhoods:
            self.next_cell[value_in] = code.pop(0)
        #Initialise the first step with the initial condition padded with sufficient zeroes
        self.step = "0"*self.r*max_steps + initial_conditions + "0"*self.r*max_steps
        self.data = [self.step]
    def process_step(self):
        result = ""
        #To maintain a closed system, the display is looped. It's calculated to be wide enough that this won't cause an issue.
        #This requires three separate for loops to ensure the correct index is being checked
        for i in range(self.r):
            result += self.next_cell[self.step[i-self.r:] + self.step[:i + self.r+1]]
        for i in range(self.r,len(self.step) - self.r):
            neighbours = self.step[i-self.r:i+self.r+1]
            result += self.next_cell[neighbours]
        for i in range(self.r):
            result += self.next_cell[self.step[i-2*self.r:] + self.step[:i+1]]
        self.step = result
        self.data.append(self.step)
    def process_steps(self, times):
        for i in range(times):
            self.process_step()
    def get_grid(self):
        return Grid(self.k, self.data)
