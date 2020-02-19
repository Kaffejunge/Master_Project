a = 4
b = 4
c = 4
x = 'acetONE'


mylist = [a, b, c]

valve_positions = ['acetone', 'h2o', 'rct_slv', 'wash_slv', 'waste',
                   'aq', 'org', 'rct', 'phase', 'sm1', 'sm2', 'sm3', 'sm4', 'naoh', 'hcl']


solvent_dict = {'acetone': [1, 0, 0, 0], 'h2o': [
    0, 1, 0, 0], 'rct_slv': [0, 0, 1, 0], 'wash_slv': [0, 0, 0, 1]}


print('h2o' in solvent_dict.keys())

SS1_dict = {'waste': [1, 1, 0], 'aq': [1, 0, 1], 'org': [
    1, 0, 0], 'rct': [0, 1, 1], 'phase': [0, 1, 0], 'connect': [0, 0, 1]}

SS2_dict = {'sm1': [1, 1, 0], 'sm2': [1, 0, 1], 'sm3': [
    1, 0, 0], 'sm4': [0, 1, 1], 'naoh': [0, 1, 0], 'hcl': [0, 0, 1]}


# if(x.lower() == 'acetone'):
#     for i in range(len(solvent_dict['acetone'])-1):
#         mylist[i] = solvent_dict['acetone'][i]
#         print(mylist[i])
