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

new_list_a = [[],[],[],[]]
new_length = [[],[],[],[]]

for k in range(len(unique_list)-1):
    for i in range(len(list_a)):
        if unique_list[k]>=list_a[i][indexa[i]]:
            if unique_list[k]<end_list[i][indexa[i]]:
                new_list_a[i].append(unique_list[k])
                new_length[i].append(unique_list[k+1]-unique_list[k])
            else:
                indexa[i] += 1

print(unique_list)
print(new_list_a)
print(new_length)


