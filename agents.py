import random
import time
import math

class Agent:
    ident = 0

    def __init__(self):
        self.id = Agent.ident
        Agent.ident += 1

    def get_chosen_action(self, state, max_depth):
        pass


class RandomAgent(Agent):
    def get_chosen_action(self, state, max_depth):
        time.sleep(0.5)
        actions = state.get_legal_actions()
        return actions[random.randint(0, len(actions) - 1)]


class GreedyAgent(Agent):
    def get_chosen_action(self, state, max_depth):
        time.sleep(0.5)
        actions = state.get_legal_actions()
        best_score, best_action = None, None
        for action in actions:
            new_state = state.generate_successor_state(action)
            score = new_state.get_score(state.get_on_move_chr())
            if (best_score is None and best_action is None) or score > best_score:
                best_action = action
                best_score = score
        return best_action

# MAXN
class MaxNAgent(Agent):
    def get_chosen_action(self, state, max_depth):
        time.sleep(0.5)
        root = self.Node(state, max_depth)
        _, action = self.maxn(self, root)  # best_child_values, best_action
        return action
    
    # pomoćna klasa za kreiranje čvora u stablu
    class Node:
        def __init__(self, state, depth):
            self.state = state                           # stanje igre u čvoru  
            self.depth = depth                           # preostala dubina
            self.chr_on_move = state.get_on_move_chr()   # igrač koji je na potezu u ovom čvoru
            self.best_child_values = None                # n-torka vrednosti najboljeg deteta
            self.best_action = None                      # akcija koja vodi do najboljeg deteta
    
    def maxn(self, node):
        #  dosegnuta maksimalna dubina ili je stanje ciljno — vraćamo n-torku vrednosti u tom čvoru i nema akcije
        if node.depth == 0 or node.state.is_goal_state():
            return node.state.get_scores(), None

        actions = node.state.get_legal_actions()
        #  nema poteza - isto kao da je stanje ciljno
        if not actions:
            return node.state.get_scores(), None

        # pretražujemo sva moguća sledeća stanja i biramo najbolje dete - ono kod kog je vrednost za chr_on_move maksimalna
        for action in actions:
            next_state = node.state.generate_successor_state(action)
            child = self.Node(next_state, node.depth - 1)
            values, _ = self.maxn(self, child)

            # MAXN kriterijum
            # ako je prvo dete koje posmatramo (best_child_values i best_action su None)
            # ili ako je kod ovog deteta vrednost za igrača na potezu veća nego kod prethodnog najboljeg deteta
            if (node.best_child_values is None and node.best_action is None) or (values[node.chr_on_move] > node.best_child_values[node.chr_on_move]): 
                # ažurira se najbolje dete čvora node
                node.best_child_values = values
                node.best_action = action
                
        return node.best_child_values, node.best_action



# MINIMAX
class MinimaxAgent(Agent):
    def get_chosen_action(self, state, max_depth):
        # igrač za kog pozivamo minimax je MAX igrač
        self.max_chr = state.get_on_move_chr()
        # drugi igrač je MIN igrač
        self.min_chr = self.get_opponent_chr(self, state, self.max_chr)
        root = self.Node(state, max_depth, True)
        _, action = self.minimax(self, root)  # best_child_value, best_action
        return action

    # funkcija koja vraća karakter drugog(MIN) igrača
    def get_opponent_chr(self, state, max_chr):
        for player in state.get_scores().keys():
            if player != max_chr:
                return player

    # pomoćna klasa za kreiranje čvora u stablu
    class Node:
        def __init__(self, state, depth, is_max_player):
            self.state = state                    # stanje igre u čvoru
            self.depth = depth                    # preostala dubina
            self.is_max_player = is_max_player    # True ako je na potezu MAX igrač, False ako je MIN igrač
            # tekst zadatka: BEST VALUE = razlika između rezultata MAX i MIN igrača
            self.best_child_value = None          # najbolji rezultat među decom
            self.best_action = None               # akcija koja vodi do najboljeg deteta

    def minimax(self, node):
        # list - dosegnuta maksimalna dubina ili je stanje ciljno — vraćamo vrednost u tom čvoru i nema akcije
        if node.depth == 0 or node.state.is_goal_state():
            return node.state.get_score(self.max_chr) - node.state.get_score(self.min_chr), None

        actions = node.state.get_legal_actions()
        # list - nema poteza - isto kao da je stanje ciljno
        if not actions:
            return node.state.get_score(self.max_chr) - node.state.get_score(self.min_chr), None

        if node.is_max_player:
            # MAX čvor: tražimo maksimum
            best = -math.inf
            for action in actions:
                next_state = node.state.generate_successor_state(action)
                child = self.Node(next_state, node.depth - 1, False) # dete je MIN čvor
                value, _ = self.minimax(self, child)
                if value > best:
                    best = value
                    node.best_action = action
            node.best_child_value = best
        else:
            # MIN čvor: tražimo minimum
            best = +math.inf
            for action in actions:
                next_state = node.state.generate_successor_state(action)
                child = self.Node(next_state, node.depth - 1, True) # dete je MAX čvor
                value, _ = self.minimax(self, child)
                if value < best:
                    best = value
                    node.best_action = action
            node.best_child_value = best

        return node.best_child_value, node.best_action

# MINIMAX sa alfa-beta odsecanjem
class MinimaxABAgent(Agent):
    def get_chosen_action(self, state, max_depth):
        time.sleep(0.5)
        # igrač za kog pozivamo minimax_ab je MAX igrač
        self.max_chr = state.get_on_move_chr()
        # drugi igrač je MIN igrač
        self.min_chr = self.get_opponent_chr(self, state, self.max_chr)
        root = self.Node(state, max_depth, True)
        # alfa = -beskonačno i beta = +beskonačno
        _, action = self.minimax_ab(self, root, -math.inf, math.inf)  # best_child_value, best_action
        return action

    # funkcija koja vraća karakter drugog(MIN) igrača
    def get_opponent_chr(self, state, max_chr):
        for player in state.get_scores().keys():
            if player != max_chr:
                return player
            
    # pomoćna klasa za kreiranje čvora u stablu
    class Node:
        def __init__(self, state, depth, is_max_player):
            self.state = state                 # stanje igre u čvoru
            self.depth = depth                 # preostala dubina
            self.is_max_player = is_max_player # True ako je na potezu MAX igrač, False ako je MIN igrač
            # tekst zadatka: BEST VALUE = razlika između rezultata MAX i MIN igrača
            self.best_child_value = None       # najbolji rezultat među decom
            self.best_action = None            # akcija koja vodi do najboljeg deteta

    def minimax_ab(self, node, alpha, beta):
        # na MAX čvoru - donja granica je alfa i pokušavamo da je podignemo
        # na MIN čvoru - gornja granica je beta i pokušavamo da je spustimo
        # kada je alpha >= beta, možemo prekinuti (dolazi do odsecanja)

        # list - dosegnuta maksimalna dubina ili je stanje ciljno — vraćamo vrednost u tom čvoru i nema akcije
        if node.depth == 0 or node.state.is_goal_state():
            return node.state.get_score(self.max_chr) - node.state.get_score(self.min_chr), None

        actions = node.state.get_legal_actions()
        # list - nema poteza - isto kao da je stanje ciljno
        if not actions:
            return node.state.get_score(self.max_chr) - node.state.get_score(self.min_chr), None

        if node.is_max_player:
            # MAX čvor: maksimizujemo vrednost i podižemo alfa
            value = -math.inf
            for action in actions:
                next_state = node.state.generate_successor_state(action)
                child = self.Node(next_state, node.depth - 1, False)   # dete je MIN
                child_value, _ = self.minimax_ab(self, child, alpha, beta)

                if child_value > value: # novo najbolje dete
                    value = child_value
                    node.best_action = action

                alpha = max(alpha, value)
                if alpha >= beta:
                    break  # beta-odsecanje

            node.best_child_value = value
            return value, node.best_action

        else:
            # MIN čvor: minimizujemo vrednost i spuštamo beta
            value = math.inf
            for action in actions:
                next_state = node.state.generate_successor_state(action)
                child = self.Node(next_state, node.depth - 1, True)    # dete je MAX
                child_val, _ = self.minimax_ab(self, child, alpha, beta)

                if child_val < value: # novo najbolje dete
                    value = child_val
                    node.best_action = action

                beta = min(beta, value)
                if alpha >= beta:
                    break  # alfa-odsecanje

            node.best_child_value = value
            return value, node.best_action