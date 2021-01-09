import sys

from crossword import *
from operator import itemgetter


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        COMPLETE

        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """

        # for each variable in the crossword...
        for var in self.crossword.variables:
            to_remove = []
            # for each word in the domain of that variable...
            for word in self.domains[var]:
                # if the word length not the same as the variable length...
                if len(word) != var.length:
                    # add it to the removal list
                    to_remove.append(word)
            # for each word in the removal list...
            for w in to_remove:
                # remove the word from the variable's domain
                self.domains[var].remove(w)

    def revise(self, x, y):
        """
        COMPLETE

        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """

        """
        if a possible word in x's domain has no corresponding
        possible word in y's domain (no letters that are the same
        in the overlapping space)...
        """

        # if no overlaps, then no change necessary, return False
        revised = False
        # (i, j) tuple where x and y overlap
        overlapPoint = self.crossword.overlaps[x, y]
        if overlapPoint == None:
            return False

        to_remove = []
        # for words in the domain of x
        for p in self.domains[x]:
            # initial amount of compatible words is 0
            compatible = 0
            # for words in the domain of y
            for q in self.domains[y]:
                # if they are not the same word...
                if p != q:
                    # if this particular p and q have the same letter in the
                    # overlap space they are compatible
                    if p[overlapPoint[0]] == q[overlapPoint[1]]:
                        compatible += 1

            # if no q is compatible with that p...
            if compatible == 0:
                # add word p to removal list
                to_remove.append(p)

        # for each item to be removed
        for item in to_remove:
            # remove it
            self.domains[x].remove(item)
            # mark that the domain has been revised
            revised = True

        return revised

    def ac3(self, arcs=None):
        """

        COMPLETE

        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """

        # add all variables to queue
        if arcs == None:
            arcs = set()
            # add all the arcs in the problem if no initial list given
            for x in self.crossword.variables:
                for y in self.crossword.variables:
                    if y != x:
                        arcs.add((x, y))

        # while you haven't run out of options...
        while len(arcs) != 0:
            # pop an arc off the queue
            a = arcs.pop()

            # if a revision gets made during the revise function...
            if self.revise(a[0], a[1]):

                # stop if you end up with an empty domain
                if len(self.domains[a[0]]) == 0:
                    return False

                # for each neighbor of the popped arc...
                for n in self.crossword.neighbors(a[0]):

                    # if the neighbor isn't the other variable in the popped arc...
                    if n != a[1]:
                        # add two arcs consisting of a[0] and the neighbor
                        arcs.add((n, a[0]))
                        arcs.add((a[0], n))

        # for each Variable in the whole crossword...
        for var in self.crossword.variables:
            # if the domain of the Variable is empty
            if len(self.domains[var]) == 0:
                # no solution
                return False

        return True

    def assignment_complete(self, assignment):
        """

        COMPLETE

        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """

        if len(self.crossword.variables) != len(assignment):
            return False
        return True

    def consistent(self, assignment):
        """

        COMPLETE

        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # for each assigned variable
        for var0 in assignment:
            for var1 in assignment:
                # skip the times it iterates to the same one
                if var0 != var1:
                    # inconsistent if value isn't distinct
                    if assignment[var0] == assignment[var1]:
                        return False
                    # inconsistent if the assignment doesn't fit in the blank
                    if len(assignment[var0]) != var0.length:
                        return False
                    # inconsistent if the overlap is incompatible
                    if self.crossword.overlaps[var0, var1]:
                        overlapPoint = self.crossword.overlaps[var0, var1]
                        if assignment[var0][overlapPoint[0]] != assignment[var1][overlapPoint[1]]:
                            return False

        return True

    def order_domain_values(self, var, assignment):
        """

        COMPLETE

        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """

        # set up list of neighbors of var, excluding those that have assignments
        neighbors = self.crossword.neighbors(var)
        for neighbor in neighbors:
            if neighbor in assignment:
                neighbors.remove(neighbor)

        unordered = []

        # for each val in the domain of the var
        for val in self.domains[var]:
            # set up counter of constraints caused
            count = 0
            # for each neighbor
            for n in neighbors:
                overlap = self.crossword.overlaps[var, n]
                # for each word in domain of neighbor
                for v in self.domains[n]:
                    # if the possible val causes a conflict with the possible v:
                    if val[overlap[0]] != v[overlap[1]]:
                        # add 1 to the conflict counter
                        count += 1
            # add val and count pairs to an unordered list
            unordered.append((val, count))

        # sort the list by the count number
        sortList = sorted(unsorted, key=itemgetter(1))

        # make a final list of the values in ascending order
        final = []
        for item in sortList:
            final.append(item[0])
        return final

    def select_unassigned_variable(self, assignment):
        """

        COMPLETE

        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """

        unsorted = []
        # for each variable in the puzzle
        for var in self.domains:
            # exclude variables already assigned
            if var not in assignment:
                # count the number of values in domain
                r = len(self.domains[var])
                # count the degree
                degree = len(self.crossword.neighbors(var))
                # add tuples to the unsorted list
                unsorted.append((var, r, degree))
        # sort in ascending order of degree
        sortList = sorted(unsorted, key=itemgetter(2))
        # sort new list in descending order of remaining values in domain
        sortList = sorted(sortList, key=itemgetter(1), reverse=True)
        return sortList[-1][0]

    def backtrack(self, assignment):
        """

        COMPLETE

        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """

        # if the assignment is complete, return
        if self.assignment_complete(assignment):
            return assignment

        # choose an unassigned variable
        var = self.select_unassigned_variable(assignment)
        # for each possible value in the variable's domain
        for val in self.domains[var]:
            # copy the assignment
            new_assignment = assignment.copy()
            # try assigning val to variable
            new_assignment[var] = val
            # if the test assignment is consistent...
            if self.consistent(new_assignment):
                # recur
                result = self.backtrack(new_assignment)
                if result is not None:
                    return result
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
