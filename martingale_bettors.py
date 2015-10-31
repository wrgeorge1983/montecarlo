__author__ = 'William R. George'


from montecarlo_core import *




class SimpleMartingaleBettor(Bettor):
    title = 'Simple Doubler Bettor'
    color = 'r'
    members = 0
    dead = 0
    net_worth_list = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.win_multiple = 1
        self.lose_multiple = 2

    def determine_wager(self):
        if not self.last_winnings:
            wager = self.last_wager * self.lose_multiple
        else:
            wager = self.initial_wager
        return min(wager, self.current_funds)


class ComplexMartingaleBettor(SimpleMartingaleBettor):
    title = 'Complex Doubler Bettor'
    color = 'c'
    members = 0
    dead = 0
    net_worth_list = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.win_multiple = self.initial_wager / self.initial_funds
        self.winstreak = 0

    def determine_wager(self):
        if not self.last_winnings:
            self.winstreak = 0
            wager = super().determine_wager()
        else:
            self.winstreak += 1
            wager = self.current_funds * self.win_multiple

        return min(wager, self.current_funds)


class ComplexBankingMartinBettor(BankingBettor, ComplexMartingaleBettor):
    title = 'Complex Banking Martin Bettor'
    color = 'g'
    members = 0
    dead = 0
    net_worth_list = []


class SimpleWorkingBettor(SimpleMartingaleBettor):
    title = 'Simple Working Bettor'
    color = 'b'
    members = 0
    dead = 0
    net_worth_list = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.lose_multiple = kwargs['lose_multiple']
        except KeyError:
            self.lose_multiple = 2

    def determine_wager(self):
        wager = super().determine_wager()
        return round(min(wager, 50))


class SimpleBankingWorkingBettor(BankingBettor, SimpleWorkingBettor):
    title = 'Simple Banking Working Bettor'
    color = 'm'
    members = 0
    dead = 0
    net_worth_list = []


class ComplexWorkingBettor(SimpleWorkingBettor, ComplexMartingaleBettor):
    title = 'Complex Working Bettor'
    color = 'm'
    members = 0
    dead = 0
    net_worth_list = []

class ComplexBankingWorkingBettor(BankingBettor, ComplexWorkingBettor):
    title = 'Complex Banking Working Bettor'
    color = 'y'
    members = 0
    dead = 0
    net_worth_list = []