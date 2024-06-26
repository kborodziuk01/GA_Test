import math

def eucl(point1,point2):

    p1x = point1[0]
    p1y = point1[1]
    p2x = point2[0]
    p2y = point2[1]

    d1 = p2x - p1x
    d2 = p2y - p1y

    d3 = d1 **2
    d4 = d2 **2

    d5 = d4+d3
    distance = math.sqrt(d5)

    return distance

def angle_from_point(point1,point2):


    point3 = [point1[0],point2[1]]


    d1 = eucl(point1,point3)
    d2 = eucl(point2,point3)


    d3 = math.atan(d2/d1) *180/math.pi

    return d3


# p1 = [3,3]
# p2 = [3,6]
#
#
# for x in range(100):
#     p2[0] = p2[0] - 1
#     print(angle_from_point(p1,p2))

