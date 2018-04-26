import math
from itertools import combinations


class QuineMccluskey():

    def __init__(self, input_function):

        self.input_function = input_function
        self.literals = int(math.ceil(math.log(self.input_function[-1]+1, 2)))
        self.minterms = self._convert_to_binary(self.input_function)

        self.groups = [[] for x in range(self.literals+1)]
        self._group_minterms()

        self.prime_implicants = self._find_prime_implicants()
        self.prime_implicant_chart = self._generate_pi_chart()

        self.solutions = [[]]
        self._solve_pi_chart()
        self.print_answer()

    def _convert_to_binary(self, input_function):

        """Groups the minterms into binary form padded with 0's to
        the left according to the number of literals."""

        return ["{0:b}".format(x).zfill(self.literals) for x in input_function]

    def _group_minterms(self):

        """Groups the different minterms according to number of 1's."""

        list(map(lambda x: self.groups[x.count('1')].append(x), self.minterms))

    def _find_prime_implicants(self):

        """Finds all the prime implicants from the given minterms."""

        implicant_table = [
            [{x: 0 for x in self.groups[i]} for i in range(self.literals+1)]
        ]
        cur_round = 1

        while len(implicant_table[-1]) != 1:

            cur_implicant_list = implicant_table[cur_round-1]
            next_implicant_list = []

            for i in range(len(cur_implicant_list) - 1):
                cur_implicant_group = {}
                for (x, y) in [
                    (a, b) for a in cur_implicant_list[i].keys()
                    for b in cur_implicant_list[i+1].keys()
                ]:
                    bit_comparison = [
                        1 if x[j] != y[j]
                        else 0 for j in range(self.literals)
                    ]
                    if bit_comparison.count(1) == 1:
                        pos = bit_comparison.index(1)
                        cur_implicant_group.update(
                            {x[:pos] + '_' + x[pos+1:]: 0}
                        )
                        (cur_implicant_list[i][x],
                         cur_implicant_list[i+1][y]) = (1, 1)
                next_implicant_list.append(cur_implicant_group)

            implicant_table.append(next_implicant_list)
            cur_round += 1

        prime_implicants = []
        for implicant_list in implicant_table:
            for implicant_group in implicant_list:
                for implicant in implicant_group.keys():
                    if implicant_group[implicant] == 0:
                        prime_implicants.append(implicant)

        return prime_implicants

    def _generate_pi_chart(self):

        """Generates and returns the prime implicant chart."""

        pi_chart = [
            [pi, [0 for pi in self.input_function]]
            for pi in self.prime_implicants
        ]

        for row in pi_chart:
            pi = row[0]
            values = [0]
            for j in range(self.literals):
                if pi[j] == '1':
                    values = list(
                        map(lambda x: x+2**(self.literals-1-j), values)
                    )
                elif pi[j] == '_':
                    values += list(
                        map(lambda x: x+2**(self.literals-1-j), values)
                    )

            for value in values:
                row[1][self.input_function.index(value)] = 1

        return pi_chart

    def _find_essential_pi(self):

        """Finds the essential prime implicants and removes them
        from the prime implicant chart. Returns False if any
        essential prime implicants were found, True otherwise."""

        if self.prime_implicant_chart != []:

            essential_prime_implicants = []
            columns_to_remove = []
            num_of_minterms = len(self.prime_implicant_chart[0][1])

            for i in range(num_of_minterms):
                r, pos = 0, -1
                for j in range(len(self.prime_implicant_chart)):
                    row = self.prime_implicant_chart[j]
                    r += row[1][i]
                    if row[1][i] == 1:
                        pos = j
                if r == 1:
                    columns_to_remove.append(i)
                    if (
                        self.prime_implicant_chart[pos][0]
                        not in essential_prime_implicants
                    ):
                        essential_prime_implicants.append(
                            self.prime_implicant_chart[pos][0]
                        )

            start, end = 0, len(self.prime_implicant_chart)
            while start < end:
                row = self.prime_implicant_chart[start]
                if row[0] in essential_prime_implicants:
                    for j in range(num_of_minterms):
                        if row[1][j] == 1 and j not in columns_to_remove:
                            columns_to_remove.append(j)
                    self.prime_implicant_chart.remove(row)
                    end -= 1
                else:
                    start += 1

            columns_to_remove.sort()
            for row in self.prime_implicant_chart:
                for col in columns_to_remove:
                    row[1].pop(col - columns_to_remove.index(col))

            self.solutions[0] += essential_prime_implicants

        return essential_prime_implicants == []

    def _remove_dominating_columns(self):

        """Removes dominating columns and returns a boolean
        indicating whether column dominance was exhibited."""

        flag = True

        if self.prime_implicant_chart != []:

            columns = [
                [row[1][i] for row in self.prime_implicant_chart]
                for i in range(len(self.prime_implicant_chart[0][1]))
            ]
            columns_to_remove = []
            for i in range(len(columns)):
                for col_to_be_compared in columns[:i] + columns[i+1:]:
                    if (
                        self._compare(columns[i], col_to_be_compared)
                        == "Dominating"
                    ):
                        if i not in columns_to_remove:
                            columns_to_remove.append(i)
            columns_to_remove.sort()
            if columns_to_remove != []:
                flag = False
            for row in self.prime_implicant_chart:
                for col in columns_to_remove:
                    row[1].pop(col - columns_to_remove.index(col))
            for col in columns_to_remove:
                columns.pop(col - columns_to_remove.index(col))

            start, end = 0, len(columns)
            while start < end and end > 1:
                if columns[start] not in columns[start+1:]:
                    start += 1
                else:
                    for row in self.prime_implicant_chart:
                        row[1].pop(start)
                    columns.pop(start)
                    flag = False
                    end -= 1

            if columns == []:
                self.prime_implicant_chart = []

        return flag

    def _remove_dominated_rows(self):

        """Removes dominated rows and returns a boolean indicating
        whether row dominance was exhibited."""

        flag = True

        if self.prime_implicant_chart != []:

            rows = [row[1] for row in self.prime_implicant_chart]
            rows_to_remove = []
            for i in range(len(rows)):
                for row_to_be_compared in rows[:i] + rows[i+1:]:
                    if (
                        self._compare(rows[i], row_to_be_compared)
                        == "Dominated"
                    ):
                        if i not in rows_to_remove:
                            rows_to_remove.append(i)
            if rows_to_remove != []:
                flag = False
            for row in rows_to_remove:
                self.prime_implicant_chart.pop(row - rows_to_remove.index(row))
                rows.pop(row - rows_to_remove.index(row))

            # Uncomment the following section to remove identical rows

            # start, end = 0, len(rows)
            # while start < end:
            #     if rows[start] not in rows[start+1:]:
            #         start += 1
            #     else:
            #         flag = False
            #         self.prime_implicant_chart.pop(start)
            #         rows.pop(start)
            #         end -= 1

        return flag

    def _compare(self, list1, list2):

        """Helper method to compare two lists and tell if they are
        dominating, dominated or Incomparable."""

        index = {0: "Incomparable", 1: "Dominated", 2: "Dominating"}
        status = 0

        if list1.count(1) < list2.count(1):
            flag = 0
            for i in range(len(list1)):
                if list1[i] == 1 and list2[i] != 1:
                    flag = 1
                    break
            if flag == 0:
                status = 1
        elif list1.count(1) > list2.count(1):
            flag = 0
            for i in range(len(list2)):
                if list2[i] == 1 and list1[i] != 1:
                    flag = 1
                    break
            if flag == 0:
                status = 2

        return index[status]

    def _solve_pi_chart(self):

        """Reduces the prime implicant chart by finding essential prime
        implicants, deleting dominating columns and deleting dominated
        rows in this order, iterated until the prime implicant chart is
        empty or can not be further reduced. If the prime implicant chart is
        still not empty after reduction, it is solved by Petrick's Method."""

        reduced = False
        while (self.prime_implicant_chart != []) and not reduced:
            reduced = self._find_essential_pi()
            reduced = self._remove_dominating_columns() and reduced
            reduced = self._remove_dominated_rows() and reduced

        if self.prime_implicant_chart != []:
            columns = [
                [row[1][i] for row in self.prime_implicant_chart]
                for i in range(len(self.prime_implicant_chart[0][1]))
            ]
            P = []
            for column in columns:
                for i in range(len(column)):
                    if column[i] == 1:
                        column[i] = i+1
                P.append(list(filter(lambda x: x != 0, column)))
            final_expression = [[elem] for elem in P[0]]
            for i in range(1, len(P)):
                new_exp = []
                for exp in final_expression:
                    for elem in P[i]:
                        if elem not in exp:
                            temp = exp + [elem]
                        else:
                            temp = exp
                        if temp not in new_exp:
                            new_exp.append(temp)
                final_expression = new_exp

            for pair in combinations(final_expression, 2):
                if (set(pair[0]).issubset(pair[1]) and
                        pair[1] in final_expression):
                            final_expression.remove(pair[1])
                elif (set(pair[1]).issubset(pair[0]) and
                      pair[0] in final_expression):
                            final_expression.remove(pair[0])

            min_cover_size = min([len(e) for e in final_expression])
            solutions = []
            for exp in final_expression:
                if len(exp) == min_cover_size:
                    solutions.append(
                        self.solutions[0] +
                        [self.prime_implicant_chart[e-1][0] for e in exp]
                    )

            self.solutions = solutions

    def print_answer(self):

        """Prints all the possible answers from the generated solutions
        using switching variables."""

        print("Following are the solutions to the given SOP function")
        variables = [chr(i) for i in range(65, 65+self.literals)]
        for solution in self.solutions:
            terms = []
            for implicant in solution:
                term = ""
                for i in range(len(implicant)):
                    if implicant[i] == '1':
                        term += variables[i]
                    elif implicant[i] == '0':
                        term += variables[i] + "'"
                terms.append(term)
            print(' + '.join(terms))


if __name__ == "__main__":

    input_function = list(
        map(int, input("Enter the boolean SOP function: ").split())
    )
    input_function.sort()

    # Example: input_function = [0,2,5,6,7,8,10,12,13,14,15]

    q = QuineMccluskey(input_function)
