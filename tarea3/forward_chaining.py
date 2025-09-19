# Provided Rules

# You are given the following production rules:

# 1.  p ∧ q → goal
# 2.  r ∧ s → p
# 3.  w ∧ r → p
# 4.  t ∧ u → q
# 5.  v     → s
# 6.  start → v ∧ r ∧ q

# Initial working memory

working_memory = {"start"}

# Track applied rules to avoid infinite loops

applied_rules = set()

# TODO: Implement each rule below

def rule1(memory):

    # Rule: p ∧ q → goal
    if 'p' in memory and 'q' in memory and 'rule1' not in applied_rules:
        memory.add('goal')
        applied_rules.add('rule1')

    pass

def rule2(memory):

    # Rule: r ∧ s → p
    if 'r' in memory and 's' in memory and 'rule2' not in applied_rules:
        memory.add('p')
        applied_rules.add('rule2')
    pass

def rule3(memory):

    # Rule: w ∧ r → p
    if 'w' in memory and 'r' in memory and 'rule3' not in applied_rules:
        memory.add('p')
        applied_rules.add('rule3')
    pass

def rule4(memory):

    # Rule: t ∧ u → q
    if 't' in memory and 'u' in memory and 'rule4' not in applied_rules:
        memory.add('q')
        applied_rules.add('rule4')

    pass

def rule5(memory):

    # Rule: v → s
    if 'v' in memory and 'rule5' not in applied_rules:
        memory.add('s')
        applied_rules.add('rule5')
    pass

def rule6(memory):

    # Rule: start → v ∧ r ∧ q
    if 'start' in memory and 'rule6' not in applied_rules:
        memory.add('v')
        memory.add('r')
        memory.add('q')
        applied_rules.add('rule6')


    pass

# List of rules in order

rules = [rule6, rule5, rule2, rule3, rule4, rule1]

# Run the production system

def run_production_system(memory):

    changed = True


    while changed:

        changed = False

        for rule in rules:

            if rule.__name__ not in applied_rules:
                rule(memory)

                print(f"Applied {rule.__name__}, memory now: {memory}")

                applied_rules.add(rule.__name__)

                changed = True

    return memory

# Run it

final_memory = run_production_system(working_memory.copy())

# Check if goal was reached

if "goal" in final_memory:

    print("\nGoal achieved!")

else:

    print("\nNo Goal not reached.")