import pygame

#Grid object used to analyse and display the results of an automaton
class Grid:
    def __init__(self, k, data):
        #Input data is a nested list (technically a list of strings, but strings are lists of characters in Python, and the Grid object treats it like an ordinary list)
        self.data = data
        self.k = k
        self.size = (len(data), len(data[0]))
        #This generator produces all the colours that will be needed, which is dependent on the number of states
        self.colours = [tuple([int(255 * (1-(i/(k-1)))) for j in range(3)]) for i in range(k)]
    #__sub__ is a python magic method which is called whenever a Grid object is subtracted from another Grid object
    def __sub__(self, other):
        #Error handling - this isn't an issue in the main code since __sub__ is only used following get_background, but it could crop up if someone other program imports a Grid object
        if self.size != other.size:
            raise ValueError("Grid sizes do not match")
        elif self.k != other.k:
            raise ValueError("Grid colours do not match")
        new_data = []
        #We want to apply the second grid as a subtraction mask, so we simply subtract the value of each cell modulo k to get the new value
        for i in range(self.size[0]):
            self_row = self.data[i]
            other_row = other.data[i]
            new_row = ""
            for j in range(self.size[1]):
                new_row += str((int(self_row[j])-int(other_row[j]))%self.k)
            new_data.append(new_row)
        #Although this returns a new Grid, using -= to assign on subtraction also uses the __sub__ method
        return Grid(self.k, new_data)
    #__eq__ is another magic method to compare equality
    def __eq__(self, other):
        return (self.data == other.data)
    def draw(self):
        #Reverse size to get width then height, which is what pygame uses
        image = pygame.Surface(self.size[::-1])
        #Draw each cell as a one-pixel rectangle
        for i in range(self.size[0]):
            row = self.data[i]
            for j in range(self.size[1]):
                pygame.draw.rect(image, self.colours[int(row[j])], (j, i, 1, 1))
        return(image)
    #get_slice returns a grid containing the cells found within the requested rectangle
    def get_slice(self, position, size):
        x,y = position
        w,h = size
        slice_data = []
        for i in range(h):
            row = self.data[y+i]
            slice_data.append(row[x:x+w])
        return Grid(self.k, slice_data)
    #get_background calculates the background pattern of the grid using the leftmost cells and returns a grid full of just that using the static method "regular"
    def get_background(self):
        bg_data = self.get_slice((0,0),(1, self.k*2)).data
        initial_data = ""
        pattern = ""
        for i in range(0,self.k):
            initial_data += (bg_data[i][0])
            if not bg_data[self.k+i][0] in pattern:
                pattern += bg_data[self.k+i][0]
        return Grid.regular(self.k, initial_data, pattern, self.size)
    #Returns the first cell found from each direction on the requested row
    def find_edges(self, row_number):
        #Use -1,-1 to represent no edges
        edges = [-1,-1]
        row = self.data[row_number]
        #reverse_row is used to check from both directions simultaneously
        reverse_row = row[::-1]
        for i in range(len(row)):
            if row[i] != "0" and edges[0] == -1:
                edges[0] = i
            if reverse_row[i] != "0" and edges[1] == -1:
                edges[1] = i
            if edges[0] != -1 and edges[1] != -1:
                break
        return tuple(edges)
    #Finds the number of connected cells of the same state from a given point, up to a provided maximum
    def fill(self, start_at, fill_cutoff):
        #First get the state we are looking for, and add the first cell to cells_to_check
        fill_colour = self.data[start_at[1]][start_at[0]]
        cells_to_check = [start_at]
        cells_in = []
        cells_out = []
        #The program performs a bredth-first search with additional constraints, as explained below
        #cells_to_check is the list of cells to be explored, cells_in is the list of cells which have been explored,
        #and cells_out is the list of cells which will never be added. By storing this we can save time on checking cells multiple times
        while len(cells_to_check) != 0 and len(cells_in) < fill_cutoff: #cells_in is capped to avoid long wait times. This is accounted for in the main program
            x,y = cells_to_check[0]
            #Only directly adjacent cells are checked - no diagonals
            next_cells = [(x+1,y), (x,y+1),(x-1,y),(x,y-1)]
            for cell in next_cells:
                #If we have already seen the cell in any capacity, skip it
                if cell in cells_in + cells_out + cells_to_check:
                    continue
                #If the cell is off the grid, skip it
                if cell[0] >= self.size[1] or cell[0]<0 or cell[1] >= self.size[0] or cell[1] < 0:
                    continue
                #If the cell is of the wrong state, skip it on all future runs
                if self.data[cell[1]][cell[0]] != fill_colour:
                    cells_out.append(cell)
                    continue
                else:
                    #We check to see if the cell has a same-state neighbour parallel to the direction we are checking in.
                    #This prevents the algorithm from following a long thin path, instead focusing on wide open spaces
                    #The exact check is different depending on if the x or y values of this cell match the ones of the cell currently being explored
                    if cell[0] != x:
                        if (cell[1] + 1 < self.size[0] and self.data[cell[1] + 1][cell[0]] == fill_colour) or (cell[1] - 1 >= 0 and self.data[cell[1] - 1][cell[0]] == fill_colour):
                            cells_to_check.append(cell)
                    elif cell[1] != y:
                        if (cell[0] + 1 < self.size[1] and self.data[cell[1]][cell[0] + 1] == fill_colour) or (cell[0] - 1 >= 0 and self.data[cell[1]][cell[0] - 1] == fill_colour):
                            cells_to_check.append(cell)
            #We remove the cell currently being explored from cells_to_check and add it to cells_in
            cells_in.append(cells_to_check.pop(0))
        return (fill_colour, cells_in)

    #Returns a Grid object which has uniform states on each step. The first few steps contain the states of initial_data, and every step after that is a loop of pattern
    @staticmethod
    def regular(k, initial_data, pattern, size):
        l,w = size #l=length, w=width
        if len(initial_data) > l:
            raise ValueError("Initial data longer than length")
        data = []
        for c in initial_data:
            data.append(c*w)
        for i in range(l-len(initial_data)):
            data.append(pattern[i%len(pattern)]*w)
        return Grid(k, data)
