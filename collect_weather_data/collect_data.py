import pandas as pd

def check_all_state_occur(state, density):
    occurred_state = set()
    all_state = set()
    state_not_listed = []
    for index, row in density.iterrows():
        occurred_state.add(row['usps'])
    for _, row in state.iterrows():
        all_state.add(row['Code'])
        if row['Code'] not in occurred_state:
            print('State not shown', row['Code'], row['State'])
            state_not_listed.append(row['State'])
    return state_not_listed, occurred_state, all_state

def collect_cities_with_states():
    city_state = {}
    density = pd.read_csv('city_density.csv')
    den = density[['name','usps']]
    den2 = pd.read_csv('city_density2.csv')
    den = pd.concat([den, den2], axis=0)
    for _, row in den.iterrows():
        city_state[row['name']] = row['usps']
    return city_state


if __name__ == '__main__':
    state = pd.read_csv('state_code.csv', usecols=['State','Code'])
    density = pd.read_csv('city_density.csv')
    den = density[['name','usps']]
    #print(occurred_state-all_state) # PR should be discarded
    den = den[den.usps != 'PR']
    den2 = pd.read_csv('city_density2.csv')
    den = pd.concat([den, den2], axis=0)
    state_not_listed, occurred_state, all_state = check_all_state_occur(state,den)
    assert(state_not_listed==[])
    assert(occurred_state==all_state)

    #den.loc[den['usps'] == some_value]