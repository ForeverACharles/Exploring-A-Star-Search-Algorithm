from asyncio import FIRST_COMPLETED
from os import get_inheritable
from pickle import TRUE
from colorama import Fore, Back, Style
#import heapq as hq
from BinaryHeap import BinaryHeap
import random
import os
import sys

from State import State

#construct a grid representing what the agent sees at a given step
def set_agent_grid(agent_grid, grid, agent_state, target_state):
    x, y = target_state.pos
    agent_grid[x][y]= 'T'
    x, y = agent_state.pos
    agent_grid[x][y] = 'A'

    #map what agent sees at current step to its previous grid
    if x - 1 >= 0 and grid[x - 1][y] != 'A' and agent_grid[x - 1][y] != 1:
        agent_grid[x - 1][y] = grid[x - 1][y]
    if x + 1 < GRID_SIZE and grid[x + 1][y] != 'A' and agent_grid[x + 1][y] != 1:
        agent_grid[x + 1][y] = grid[x + 1][y]
    if y - 1 >= 0 and grid[x][y - 1] != 'A'  and agent_grid[x][y - 1] != 1:
        agent_grid[x][y - 1] = grid[x][y - 1]
    if y + 1 < GRID_SIZE and grid[x][y + 1] != 'A' and agent_grid[x][y + 1] != 1:
        agent_grid[x][y + 1] = grid[x][y + 1]

    return agent_grid

#implementation of repeated forward A*
def forward_astar(grid, agent_pos, target_pos, size, g_tie_breaker):
    #os.system('cls')

    agent_state = State(agent_pos)
    agent_state.f_value = get_f_value(agent_pos, agent_pos, target_pos)
    target_state = State(target_pos)

    global GRID_SIZE
    global GRID
    global COUNTER
    FIRST_PRINT = True
    
    GRID_SIZE = size
    GRID = [[0] * GRID_SIZE for i in range(GRID_SIZE)]
    GRID = set_agent_grid(GRID, grid, agent_state, target_state)
    path_grid = grid.copy()
    COUNTER = 0
    EXPANSIONS = 0
    
    #print_grid(GRID, agent_state, target_state.pos)
    
    while agent_state.pos != target_pos:
        COUNTER = COUNTER + 1
        agent_state.g_cost = 0
        agent_state.search = COUNTER

        target_state.g_cost = GRID_SIZE**2
        target_state.search = COUNTER

        #open list is a min heap representing list of tuples (primary key, 2ndary key, order of insertion, value) using key to maintain minimum ordering in the heap
        open_list = BinaryHeap()
        closed_list = []
        order = 0   #order is extremely important for breaking ties for heap insertion, without it the program will crash
        agent_state.f_value = agent_state.g_cost + manhattan_distance(agent_pos, target_pos)
        heap_insert(agent_state, order, open_list, g_tie_breaker)
		
        # get shortest path for what the agent observes in its current grid
        EXPANSIONS = determine_path(agent_state, target_state, order, open_list, closed_list, g_tie_breaker, EXPANSIONS)
        if len(open_list.heap) == 0:
            print("Agent cannot reach the Target")
            return [-COUNTER, EXPANSIONS]
        
        #trace path from target to agent
        while agent_state.pos != target_pos:
        
            #print_grid(GRID, agent_state, target_state.pos)
            current = target_state
            
            if current.prev.pos == agent_state.pos:
                x, y = agent_state.pos
                GRID[x][y] = 0
                agent_state.pos = current.pos
                GRID = set_agent_grid(GRID, grid, agent_state, target_state)
                x, y = current.pos
                path_grid[x][y] = '*'
            else:
                x = 0
                y = 0
                while current.prev.prev != None:
                    if current.prev.prev.pos == agent_state.pos:
                           x, y = current.prev.pos
                           break
                    else: current = current.prev
                
                #move the agent if possible
                if grid[x][y] == 1: 
                    break
                path_grid[x][y] = '*'
                
                x, y = agent_state.pos
                GRID[x][y] = 0
                agent_state.pos = current.prev.pos
                current.prev = current.prev.prev
                GRID = set_agent_grid(GRID, grid, agent_state, target_state)

            FIRST_PRINT = print_grid(GRID, agent_state, target_state.pos, FIRST_PRINT)
    
    #get_path_grid(path_grid, grid, agent_pos, target_pos)
    FIRST_PRINT = True
    return [COUNTER, EXPANSIONS]

#get shortest path for what the agent observes in its current grid
def determine_path(agent_state, target_state, order, open_list, closed_list, g_tie_breaker, expansions):
    # while g(goal_state) > minimum f value state in the heap
    #print(target_state.g_cost)
    while len(open_list.heap) > 0 and target_state.g_cost > open_list.heap[0][0]:
        state = open_list.pop()[3]
        expansions = expansions + 1
        #mark the minmum f value state as visited
        closed_list.append(state)
        #print("expanding: " + state.to_string())
        actions = get_actions(state, closed_list) 
        #actions represent possible successor states that can be visited following this current state
        for action_state in actions:
        
            #agent found the target, break out of loop
            if action_state.pos == target_state.pos:
                target_state.prev = state
                return expansions

            if action_state.search < COUNTER:
                action_state.g_cost = GRID_SIZE**2
                action_state.search = COUNTER

            agent_action_cost = manhattan_distance(state.pos, action_state.pos)
            if action_state.g_cost > state.g_cost + agent_action_cost:
                
                #set updated g cost for next state and pointer back to source state
                action_state.g_cost = state.g_cost + agent_action_cost
                action_state.prev = state

                #remove the action from the open list if it currently aready exists
                removed = check_and_remove(action_state, open_list)
                #insert the successor state into the open list
                
                order = order + 1
                action_state.f_value = action_state.g_cost + manhattan_distance(action_state.pos, target_state.pos)
                heap_insert(action_state, order, open_list, g_tie_breaker)
                
        #for action_state in actions:
            #print("added: " + action_state.to_string())
        #print()

    return expansions
    
def backward_astar(grid, agent_pos, target_pos, size, g_tie_breaker):
    #os.system('cls')

    agent_state = State(agent_pos)
    agent_state.f_value = get_f_value(agent_pos, agent_pos, target_pos)
    target_state = State(target_pos)
    target_state.f_value = get_f_value(agent_pos, target_pos, target_pos)

    global GRID_SIZE
    global GRID
    global COUNTER
    FIRST_PRINT = True
    
    GRID_SIZE = size
    GRID = [[0] * GRID_SIZE for i in range(GRID_SIZE)]
    GRID = set_agent_grid(GRID, grid, agent_state, target_state)
    path_grid = grid.copy()
    COUNTER = 0
    EXPANSIONS = 0

    #print_grid(GRID, agent_state, target_state.pos)
    
    while agent_state.pos != target_pos:
        COUNTER = COUNTER + 1
        agent_state.g_cost = GRID_SIZE**2
        agent_state.search = COUNTER

        target_state.g_cost = 0
        target_state.search = COUNTER

        #open list is a min heap representing list of tuples (primary key, 2ndary key, order of insertion, value) using key to maintain minimum ordering in the heap
        open_list = BinaryHeap()
        closed_list = []
        order = 0   #order is extremely important for breaking ties for heap insertion, without it the program will crash
        heap_insert(target_state, order, open_list, g_tie_breaker)

        #get shortest path for what the agent observes in its current grid
        EXPANSIONS = backward_determine_path(agent_state, target_state, order, open_list, closed_list, g_tie_breaker, EXPANSIONS)
        if len(open_list.heap) == 0:
            print("Agent cannot reach the Target")
            return [-COUNTER, EXPANSIONS]
        
        next_state = agent_state.prev
        while agent_state.pos != target_pos:
            
            #trace path from target to agent
            x, y = next_state.pos
            if grid[x][y] == 1:
                break
            path_grid[x][y] = '*'
            
            #move the agent
            x, y = agent_state.pos
            GRID[x][y] = 0
            agent_state.pos = next_state.pos
            
            GRID = set_agent_grid(GRID, grid, agent_state, target_state)
            next_state = next_state.prev
            FIRST_PRINT = print_grid(GRID, agent_state, target_state.pos, FIRST_PRINT)
            
    #get_path_grid(path_grid, grid, agent_pos, target_pos)
    FIRST_PRINT = True
    return [COUNTER, EXPANSIONS]
    
def backward_determine_path(agent_state, target_state, order, open_list, closed_list, g_tie_breaker, expansions):
    # while g(agent_state) < minimum f value state in the heap
    while len(open_list.heap) > 0 and agent_state.g_cost > open_list.heap[0][0]:
        state = open_list.pop()[3]
        expansions = expansions + 1
        #mark the minmum f value state as visited
        closed_list.append(state)
        #print("expanding: " + state.to_string())
        actions = get_actions(state, closed_list)
        #actions represent possible successor states that can be visited following this current state
        for action_state in actions:
            #agent found the target, break out of loop
            if action_state.pos == agent_state.pos:
                agent_state.prev = state
                return expansions

            if action_state.search < COUNTER:
                action_state.g_cost = GRID_SIZE**2
                action_state.search = COUNTER

            #agent_action_cost = get_g_cost(target_state.pos, action_state.pos)
            agent_action_cost = manhattan_distance(state.pos, action_state.pos)
            #if action_state.g_cost > state.g_cost + agent_action_cost:
            if action_state.g_cost > target_state.g_cost + agent_action_cost:

                #set updated g cost for next state and pointer back to source state
                
                action_state.g_cost = target_state.g_cost + agent_action_cost
                action_state.prev = state

                #remove the action from the open list if it currently aready exists
                removed = check_and_remove(action_state, open_list)

                #insert the successor state into the open list
                order = order + 1
                #action_state.f_value = get_f_value(agent_state.pos, action_state.pos, target_state.pos)
                action_state.f_value = action_state.g_cost + manhattan_distance(action_state.pos, target_state.pos)
                heap_insert(action_state, order, open_list, g_tie_breaker)
                
               
        #for action_state in actions:
            #print("added: " + action_state.to_string())
        #print()

    return expansions
    
def adaptive_set_heuristic(agent_state):
    heuristic_grid = [[0] * GRID_SIZE for i in range(GRID_SIZE)]
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            cur_state = State([i, j])
            heuristic_grid[i][j] = get_g_cost(agent_state.pos, cur_state.pos)
        #print(heuristic_grid[i])
    return heuristic_grid

def adaptive_astar(grid, agent_pos, target_pos, size, g_tie_breaker):
    #os.system('cls')

    agent_state = State(agent_pos)
    agent_state.f_value = get_f_value(agent_pos, agent_pos, target_pos)
    target_state = State(target_pos)

    global GRID_SIZE
    global GRID
    global COUNTER
    FIRST_PRINT = True
    
    GRID_SIZE = size
    GRID = [[0] * GRID_SIZE for i in range(GRID_SIZE)]
    GRID = set_agent_grid(GRID, grid, agent_state, target_state)
    path_grid = grid.copy()
    COUNTER = 0
    EXPANSIONS = 0

    heuristic_grid = adaptive_set_heuristic(target_state)

    #print_grid(GRID, agent_state, target_state.pos)
    
    while agent_state.pos != target_pos:
        COUNTER = COUNTER + 1
        agent_state.g_cost = 0
        agent_state.search = COUNTER

        target_state.g_cost = GRID_SIZE**2
        target_state.search = COUNTER

        #open list is a min heap representing list of tuples (primary key, 2ndary key, order of insertion, value) using key to maintain minimum ordering in the heap
        open_list = BinaryHeap()
        closed_list = []
        order = 0   #order is extremely important for breaking ties for heap insertion, without it the program will crash
        heap_insert(agent_state, order, open_list, g_tie_breaker)

        #get shortest path for what the agent observes in its current grid
        EXPANSIONS = adaptive_determine_path(agent_state, target_state, order, open_list, closed_list, g_tie_breaker, EXPANSIONS, heuristic_grid)
        if len(open_list.heap) == 0:
            print("Agent cannot reach the Target")
            return [-COUNTER, EXPANSIONS]
        
        #trace path from target to agent
        while agent_state.pos != target_pos:
        
            #print_grid(GRID, agent_state, target_state.pos)
            current = target_state
            
            if current.prev.pos == agent_state.pos:
                x, y = agent_state.pos
                GRID[x][y] = 0
                agent_state.pos = current.pos
                GRID = set_agent_grid(GRID, grid, agent_state, target_state)
                x, y = current.pos
                path_grid[x][y] = '*'
               
            else:
                x = 0
                y = 0
                while current.prev.prev != None:
                    if current.prev.prev.pos == agent_state.pos:
                           x, y = current.prev.pos
                           break
                    else: current = current.prev
                
                #move the agent if possible
                if grid[x][y] == 1: 
                    break
                path_grid[x][y] = '*'
                
                x, y = agent_state.pos
                GRID[x][y] = 0
                agent_state.pos = current.prev.pos
                current.prev = current.prev.prev
                GRID = set_agent_grid(GRID, grid, agent_state, target_state)

            FIRST_PRINT = print_grid(GRID, agent_state, target_state.pos, FIRST_PRINT)
    
    #get_path_grid(path_grid, grid, agent_pos, target_pos)
    #os.system('cls')
    return [COUNTER, EXPANSIONS]
    
def adaptive_determine_path(agent_state, target_state, order, open_list, closed_list, g_tie_breaker, expansions, heuristic_grid):
    # while g(goal_state) > minimum f value state in the heap
    #print(target_state.g_cost)
    agent_state.g_cost = 0
    while len(open_list.heap) > 0 and target_state.g_cost > open_list.heap[0][0]:
        state = open_list.pop()[3]
        expansions = expansions + 1
        #mark the minmum f value state as visited
        closed_list.append(state)
        #print("expanding: " + state.to_string())
        actions = get_actions(state, closed_list)
        #actions represent possible successor states that can be visited following this current state
        for action_state in actions:
            #agent found the target, break out of loop
            if action_state.pos == target_state.pos:
                target_state.prev = state
                action_state.g_cost = state.g_cost + 1

                #UPDATE HEURISTICS
                #print("TARGET HAS G_COST OF: "+ str(action_state.g_cost))
                for i in closed_list:
                    heuristic_grid[i.pos[0]][i.pos[1]] = action_state.g_cost - i.g_cost 
                #for i in heuristic_grid:
                #    print(i)          
                #print("------------------------------")       

                return expansions

            if action_state.search < COUNTER:
                action_state.g_cost = GRID_SIZE**2
                action_state.search = COUNTER

            #agent_action_cost = get_g_cost(state.pos, action_state.pos)
            agent_action_cost = manhattan_distance(state.pos, action_state.pos)
            if action_state.g_cost > state.g_cost + agent_action_cost:
                
                #set updated g cost for next state and pointer back to source state
                action_state.g_cost = state.g_cost + agent_action_cost
                action_state.prev = state
                #print("G COST: "+ str(action_state.g_cost))

                #remove the action from the open list if it currently aready exists
                check_and_remove(action_state, open_list)
                
                #insert the successor state into the open list
                order = order + 1
                #print("f-value: "+ str(heuristic_grid[action_state.pos[0]][action_state.pos[1]] + action_state.g_cost))
                action_state.f_value = heuristic_grid[action_state.pos[0]][action_state.pos[1]] + action_state.g_cost
                heap_insert(action_state, order, open_list, g_tie_breaker)
                
               
        #for action_state in actions:
            #print("added: " + action_state.to_string())
        #print()

    return expansions

#checks neighbors of a state for non-blocked states, returns a list of unblocked state tuples
def get_actions(state, closed_list):
    x, y = state.pos
    UP = [x - 1, y]
    up_state = State(UP)
    DOWN = [x + 1, y]
    down_state = State(DOWN)
    LEFT = [x, y - 1]
    left_state = State(LEFT)
    RIGHT = [x, y + 1]
    right_state = State(RIGHT)

    neighbors = []
    #check up direction
    if x - 1 >= 0 and GRID[x - 1][y] != 1 and not check_list(up_state, closed_list):
        neighbors.append(up_state)
    #check down direction
    if x + 1 < GRID_SIZE and GRID[x + 1][y] != 1 and not check_list(down_state, closed_list):
        neighbors.append(down_state)
    #check left direction
    if y - 1 >= 0 and GRID[x][y - 1] != 1 and not check_list(left_state, closed_list):
        neighbors.append(left_state)
    #check right direction
    if y + 1 < GRID_SIZE and GRID[x][y + 1] != 1 and not check_list(right_state, closed_list):
        neighbors.append(right_state)
        
    return neighbors

#insert a state into the min heap open_list as a tuple, order of values in the tuple matters for breaking ties
def heap_insert(state, order, open_list, g_tie_breaker):
    # g_tie_breaker value of -1 means higher g costs used to break ties, value of 1 means lower ones are used
    tuple = (state.f_value, state.g_cost * g_tie_breaker, order, state)
    open_list.insert(tuple)
    #hq.heappush(open_list, tuple)

def check_list(action_state, list):
    for state in list:
        if state.pos == action_state.pos: return True
    return False

def check_and_remove(action_state, list):
    for tuple in list.heap:
        if tuple[3].pos == action_state.pos:
            list.heap.remove(tuple)
            list.reheap(0)
            return True
    return False

def manhattan_distance(start_pos, end_pos):
    return abs(start_pos[0] - end_pos[0]) + abs(start_pos[1] - end_pos[1])

def get_g_cost(agent_pos, state_pos):
    return manhattan_distance(agent_pos, state_pos)

def get_f_value(agent_pos, state_pos, target_pos):
        # f(s) = g(s) + h(s)
    return get_g_cost(agent_pos, state_pos) + manhattan_distance(state_pos, target_pos)

def print_list(list):
    for (f, o, state) in list:
        print(state.to_string() )

def print_grid(grid, agent_state, target_pos, FIRST_PRINT):

    output = "Size:[" + str(GRID_SIZE) + ", " + str(GRID_SIZE) + "]\n"
    output += "Agent: " + str(agent_state.pos) + ", Target: " + str(target_pos) + "\n"

    for column in range(GRID_SIZE):
        if 3 - len(str(column)) == 2:
            output += " " + str(column) + " "
            #print(" " + str(column), end=" ")
        elif 3 - len(str(column)) == 1:
            output += str(column) + " "
            #print(str(column), end=" ")
        else: 
            output += str(column)
            #print(str(column), end="")

   
    output += "\n"
    #print()

    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            cell = grid[y][x]
            if cell == 1: 
                output += f"{Fore.BLACK}{Back.BLACK}[ ]" + f"{Style.RESET_ALL}"
                #print(f"{Fore.BLACK}{Back.BLACK}[ ]" + f"{Style.RESET_ALL}", end="")
            elif cell == 'A':
                output += f"{Fore.WHITE}{Back.RED}[" + str(cell) + "]" + f"{Style.RESET_ALL}"
                #print(f"{Fore.WHITE}{Back.RED}[" + str(cell) + "]" + f"{Style.RESET_ALL}", end="")
            elif cell == 'T':
                output += f"{Fore.WHITE}{Back.BLUE}[" + str(cell) + "]" + f"{Style.RESET_ALL}"
                #print(f"{Fore.WHITE}{Back.RED}[" + str(cell) + "]" + f"{Style.RESET_ALL}", end="")
            elif cell == '*':
                output += f"{Fore.WHITE}{Back.WHITE}[" + f"{Fore.RED}{Back.WHITE}" + str(cell) + f"{Fore.WHITE}{Back.WHITE}]" + f"{Style.RESET_ALL}"
                #print(f"{Fore.BLACK}{Back.WHITE}[" + str(cell) + "]" + f"{Style.RESET_ALL}", end="")
            else:
                output += f"{Fore.WHITE}{Back.WHITE}[ ]" + f"{Style.RESET_ALL}"
        output += " " + str(y) + "\n"
        #print(" " + str(y))

    if(not FIRST_PRINT):
        sys.stdout.write("\033[F"*(GRID_SIZE + 3))

    print(output, end="")    
    return False

def get_path_grid(path_grid, grid, agent_pos, target_pos):
    x, y = agent_pos
    path_grid[x][y] = 'A'
    x, y = target_pos
    path_grid[x][y] = 'T'

    for column in range(GRID_SIZE):
        if 3 - len(str(column)) == 2:
            print(" " + str(column), end=" ")
        elif 3 - len(str(column)) == 1:
            print(str(column), end=" ")
        else: print(str(column), end="")
    print()

    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            cell = path_grid[y][x]
            if cell == 1: 
                print(f"{Fore.BLACK}{Back.BLACK}[ ]" + f"{Style.RESET_ALL}", end="")
            elif cell == 'A' or cell == 'T':
                print(f"{Fore.WHITE}{Back.RED}[" + str(cell) + "]" + f"{Style.RESET_ALL}", end="")
            elif cell == '*':
                print(f"{Fore.BLACK}{Back.WHITE} " + str(cell) + " " + f"{Style.RESET_ALL}", end="")
            else:
                print(f"{Fore.WHITE}{Back.WHITE}[ ]" + f"{Style.RESET_ALL}", end="")
        print(" " + str(y))
    print()
