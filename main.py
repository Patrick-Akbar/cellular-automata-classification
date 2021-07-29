import pygame, os, sys
from Automaton import Automaton, padNumber

#Total number of steps an automaton is run for
max_steps = 300
#Total number of cells which can be filled by a Grid object's fill function 
fill_cutoff = 500


#Function to generate every intial condition of the given size or less in k states. Uses recursion to get conditions less than the length requested
def generate_ics(k, size):
    if size == 1:
        return [str(i) for i in range(1,k)]
    else:
        lesser_ics = generate_ics(k, size-1)
        current_ics = []
        for ic in lesser_ics:
            for colour in range(1,k):
                current_ics.append(str(colour) + padNumber(ic, size - 1))
        return lesser_ics + current_ics


#Creates a directory to write images to a file. Images are sorted based on the maximum number of steps and the initial condition
#This function is currently not used
def create_path(ic):
    #Creates each directory level in turn as required
    if not os.path.exists("rules"):
        os.mkdir("rules")
    superdir = "rules/max_" + str(max_steps)
    if not os.path.exists(superdir):
        os.mkdir(superdir)
    image_path = superdir + "/" + ic
    if not os.path.exists(image_path):
        os.mkdir(image_path)
    return image_path


#Calculates the growth rate of a given Grid object
#Returns the gradients from each side as a tuple
def get_shape(grid):
    bg = grid.get_background()
    #Removing the background gives a more accurate assessment of the gradient
    #This also ensures any non-background state is nonzero
    grid -= bg
    points = []
    check_at = [0, max_steps]
    for i in check_at:
        point = grid.find_edges(i)
        if point == (-1,-1):
            #If no point is found at either location, the grid does not contain a solid shape
            return
        else:
            points.append(point)
    growth_rate = tuple([(points[0][i] - points[1][i])/(grid.size[0]-1) for i in range(2)])
    return growth_rate

#Checks whether a given Grid object contains a simple repeating pattern
def check_simple_pattern(grid, growth_rate):
    #max_pattern defines the maximum size of pattern which is checked for. The minimum is always 2x2, because a 1x1 pattern will also form a 2x2 pattern
    max_pattern = (5,15)
    h, w = grid.size
    #This generator uses (j,i) so the height changes less frequently than the width (i.e the list goes [(2,2),(3,2),(4,2)...(2,3),(3,3),...])
    #   because the cells above are checked first. As a result, that check is more likely to indicate the presence of a pattern, so the program will
    #   spend more time on a height range which is successful rather than skippig around 
    pattern_sizes = [(j,i) for i in range(2,max_pattern[0]+1) for j in range(2, max_pattern[1]+1)]
    half_match = False
    if growth_rate[0] > 0.1:
        #The program checks the bottom row, 20% in from the edge
        base_start =(int(w / 2 * (1 - growth_rate[0] * 0.8)),h-1)
        for size in pattern_sizes:
            start = (base_start[0], base_start[1] - size[1])
            pattern_slice = grid.get_slice(start, size)
            #First check the cells above
            compare_slice = grid.get_slice((start[0],start[1]-size[1]),size)
            if not pattern_slice == compare_slice:
                continue
            #Then check the adjacent cells - we want at least 80% of the length to be this same pattern
            #First check left from the start
            match_count = 0
            x = start[0]
            while pattern_slice == compare_slice:
                match_count += 1
                x -= size[0]
                compare_slice = grid.get_slice((x,start[1]),size)
            #Then check right from the start, with a buffer of size[0] to ensure the start pattern isn't counted twice
            x = start[0] + size[0]
            compare_slice = grid.get_slice((x,start[1]),size)
            while pattern_slice == compare_slice:
                match_count += 1
                x += size[0]
                compare_slice = grid.get_slice((x,start[1]),size)
            #If it matched at least 80% of the length along the pattern, that's sufficient to classify it as a simple repeating pattern
            if match_count * size[0] >= ((growth_rate[0]+growth_rate[1]) / 2) * w  * 0.8 : 
                return True
            #If it didn't, the automaton might still be a simple repeating pattern if it is asymmetrical.
            #We should only check from the othe side if at least 80% of the pattern was matched in the right hand half of the structure
            elif match_count * size[0] >= (growth_rate[0] / 2) * w  * 0.8 :
                half_match = True
                break
        if not half_match: #If it didn't at least match half, it cannot be a simple pattern
            return False
    #If the program reaches here, either the other side had gradient < 0.1 or the it matched half
    #As a result, if this side matches (with the same process as above) the automaton can be classified as a simple repeating pattern
    if growth_rate[1] > 0.1:
        base_start =(int(w / 2 * (1 + growth_rate[1] * 0.8)),h-1)
        for size in pattern_sizes:
            start = (base_start[0], base_start[1] - size[1])
            pattern_slice = grid.get_slice(start, size)
            compare_slice = grid.get_slice((start[0],start[1]-size[1]),size)
            if not pattern_slice == compare_slice:
                continue
            match_count = 0
            x = start[0]
            while pattern_slice == compare_slice:
                match_count += 1
                x += size[0]
                compare_slice = grid.get_slice((x,start[1]),size)
            x = start[0] - size[0]
            compare_slice = grid.get_slice((x,start[1]),size)
            while pattern_slice == compare_slice:
                match_count += 1
                x -= size[0]
                compare_slice = grid.get_slice((x,start[1]),size)
            #Here we only check for half, since if the whole matched it would have done so in the first half of this function
            if match_count * size[0] >= (growth_rate[1] / 2) * w  * 0.8 :
                return True
    return False

#This function checks if the grid contains a fractal pattern. It takes quite a bit of time, so it should be done after the
#   simple repeating pattern check
def check_fractal(grid, growth_rate):
    #c is the spacing of the points the Grid's fill method is called at
    c = 50
    h, w = grid.size
    prelim_points = [(i*c,j*c) for i in range(w//c) for j in range(h//c)]
    points_to_check = []
    for point in prelim_points:
        #We only check the points that are within the shape produced by the automaton
        if ((w/2) - point[0] < point[1] * growth_rate[0]) and (point[0] - (w/2) < point[1] * growth_rate[1]):
            points_to_check.append(point)
    filled_points = {}
    max_size = 0
    for point in points_to_check:
        already_used = False
        #If a point has been found by a call to the fill method already, we don't call it again in order to save time
        for k in filled_points.keys():
            if point in filled_points[k]:
                already_used = True
                break
        if already_used:
            continue
        #The eventual decision is made based on the ratio of maximum possible points that could be filled and the number that were actually filled
        #This first number is dependent on the number of points the method is called at, which is why it (max_size) is increased at this stage
        max_size += fill_cutoff
        #result is a tuple of the colour found and a list of the points filled. We store the data in a dictionary, with the colour as a key
        result = grid.fill(point, fill_cutoff)
        if result[0] in filled_points.keys():
            filled_points[result[0]] = filled_points[result[0]] + result[1]
        else:
            filled_points[result[0]] = result[1]
    summary = {}
    
    for colour in filled_points.keys():
        #Converting to a dictionary and back again removes duplicated points
        #If the threshold of 1/3 of the maximum possible cells is passed, the automaton is classified as a fractal
        if len(list(dict.fromkeys(filled_points[colour]))) >= max_size/3:
            return True
    return False

#This function performs each of the analysis functions above in order, and reurns a number indicating the classification of the automaton
#These numbers correspond to the list behaviour_types below
def analyse_grid(grid):
    shape = get_shape(grid)
    is_fractal = False
    if shape == None:
        return 0
    #We compare the difference between the two gradients here - if it is less than 0.2, the automaton is classified as a line
    #The reason they are added is because the gradients are signed based on their direction. Outwards is positive, inwards is negative
    elif (shape[0] + shape[1] < 0.2):
        return 1
    else:
        #If there is a gradient and the difference is at least 0.2, the automaton forms a 2D shape
        bg = grid.get_background()
        grid -= bg
        if (check_simple_pattern(grid, shape)):
            return 2
        elif(check_fractal(grid, shape)):
            return 3
        else:
            return 4

#behaviour types is textual description of each of the five possibilities for the behaviour of the automaton itself
behaviour_types = [
    "All active cells disappear before the end of the program.",
    "The code produces a line.",
    "The code produces a simple repeating pattern.",
    "The code produces a nested fractal pattern.",
    "The code produces a complex design which doesn't fall into any of the other categories.",]


#This function runs an automaton, analyses its behaviour, and prints the result
def analyse_code(k,r,code, ic):
    rule = Automaton(k, r, code, ic, max_steps)
    rule.process_steps(max_steps)
    result = analyse_grid(rule.get_grid())
    #Read back what the program is doing to ensure the user's input was what they intended
    print("The code " + str(code) + " with " + str(k) + " colours and a range of " + str(r) + " exhibits the following behaviour with initial conditions " + ic + ":")
    print(behaviour_types[result])

#analyse_rule runs any elementary automaton on all 16 simple initial conditions at most 5 cells wide
#This is a separate function to analyse_code because the text output is different
def analyse_rule(code):
    ics = generate_ics(2, 5)
    record = []
    for ic in ics:
        rule = Automaton(2, 1, code, ic, max_steps)
        rule.process_steps(max_steps)
        record.append(analyse_grid(rule.get_grid()))
    count = {}
    #Keep track of each result produced, and total the number of each
    for entry in list(dict.fromkeys(record)):
        count[entry] = record.count(entry)
    #We now have different responses for if the same behaviour is always produced, or if it there are multiple different ones
    if len(count.keys()) == 1:
        print("The code " + str(code) + " with 2 colours and a range of 1 always produces the same result from simple initial conditions.")
        print(behaviour_types[record[0]])
    else:
        print("The code " + str(code) + " with 2 colours and a range of 1 exhibits different behaviour depending on its initial conditions.")
        key_val_pairs = [(k, count[k]) for k in count.keys()]
        #Sort the behaviours in order of frequency
        key_val_pairs.sort(reverse=False, key=lambda pair: pair[1])
        for pair in key_val_pairs:
            print(behaviour_types[pair[0]] + " This occurred " + str(pair[1]) + " times.")

instructions = "The automaton should be entered as the number of states, radius of neighbourhood, and code, separated by commas. For example, \"2,1,30\" produces the elementary automaton Rule 30"
print(instructions)
#This is the main input loop. Note that it pauses while the pygame window is open
while True:
    inp = input("\nPlease enter the desired automaton: ")
    #"q" is used to quit
    if inp.lower() == "q":
        break
    #Simple input handling to stop the program from crashing
    try:
        k,r,code = inp.split(",")
        max_code = max_code = int(k)**(int(k)**(2*int(r)+1)) - 1
        if (int(code) > max_code):
            print("This code is too large. The maximum allowed code for these values is " + str(max_code))
            continue
    except:
        print(instructions)
        continue
    #If the user requested an elementary automaton, offer to run all simple initial conditions (size <=5)
    all_ics = False
    if (int(k) == 2 and int(r) == 1):
        process_all = input("Do you want to analyse all simple initial conditions for this automaton? y/n ")
        if process_all.lower() == "y":
            all_ics = True
    #If we aren't running all ics, request the desired ic
    if not all_ics:
        ic = input("Please enter the desired initial conditions: ")
        #Check the condition contains integers less than k. Length doesn't matter
        try:
            invalid_digit = False
            for digit in ic:
                if (int(digit) >= int(k)):
                    print("This initial condition is invalid, please try again")
                    invalid_digit = True
                    break
            if invalid_digit: continue
        except:
            print("This initial condition is invalid, please try again")
            continue
        analyse_code(int(k),int(r),int(code), ic)
    else:
        #analyse_rule handles printing text itself, so 
        analyse_rule(int(code))
    #We run the automaton one more time to display it, using the initial condition of just "1" if all ics were run
    ru = Automaton(int(k), int(r), int(code), "1" if all_ics else ic, max_steps)
    ru.process_steps(max_steps)
    grid = ru.get_grid()
    image = grid.draw()
    #Scale the image up two times. This value can be changed if desired
    scale = 2
    screen_size = tuple([x * scale for x in grid.size[::-1]])
    screen = pygame.display.set_mode(screen_size)
    #Draw the image to the pygame window
    screen.blit(pygame.transform.scale(image, screen_size), (0,0))
    pygame.display.flip()
    print("Drawn image. Close the pygame window or press the escape key when it has focus to continue")
    #Uncomment this line to save the most recent image to the file "tmp.png" in the current directory
    #pygame.image.save(screen, "tmp.png")

    #This loop keeps the pygame window open until the user closes it or presses the escape key
    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                run = False
        pygame.display.flip()
    pygame.display.quit()

#Close down pygame gracefully
pygame.quit()
sys.exit()
