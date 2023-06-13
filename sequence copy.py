list_a = [[2,5,7,16],[1,4,8,12]]
length=[[2,1,5,5],[2,3,3,5]]

# list_a = [[2,5,7,16],[2,5,7,16]]
# length=[[2,1,5,5],[2,1,5,5]]

end_list = []

for ii, sub_list in enumerate(list_a):
    temp_list = []
    for cc, val in enumerate(sub_list):
        temp_list.append(val+length[ii][cc])
    end_list.append(temp_list)

flat_list = [element for innerList in list_a+end_list for element in innerList]
flat_list.sort()
unique_list = list(set(flat_list))

indexa = [i*0 for i in range(len(list_a))]

new_list_a = []
new_length = []
pins_seq = []

for k in range(len(unique_list)-1):
    temp = []
    for i in range(len(list_a)):
        if unique_list[k]>=list_a[i][indexa[i]]:
            if unique_list[k]<end_list[i][indexa[i]]:
                if unique_list[k] not in new_list_a:
                    new_list_a.append(unique_list[k])
                    new_length.append(unique_list[k+1]-unique_list[k])
                temp.append(i)
            else:
                indexa[i] += 1
    pins_seq.append(temp)

# print(unique_list)
print(new_list_a)
print(new_length)
print(pins_seq)


