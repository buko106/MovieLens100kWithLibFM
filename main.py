import os
import argparse
import random
import numpy as np

# argparse configurations
desc="Script for generating train/test dataset of MovieLens100k(https://grouplens.org/datasets/movielens/) for libFM(http://libfm.org/) and libffm-regression(https://www.csie.ntu.edu.tw/~cjlin/libffm/)"
parser = argparse.ArgumentParser(description=desc)
parser.add_argument("--prefix-train", type = str, default="train_", help="default='train_'")
parser.add_argument("--prefix-test" , type = str, default="test_" , help="default='test_'")
parser.add_argument("--dataset"     , metavar="DATA",type = str, default="dataset/",help="default='dataset/'" )
parser.add_argument("-o", "--output", metavar="DIR" ,type = str, default="output" , help="default='output/'")
parser.add_argument("-t", "--timestamp", action="store_true")
parser.add_argument("-g", "--genre", action="store_true")
parser.add_argument("-a", "--age", action="store_true")
parser.add_argument("-s", "--sex", action="store_true")
parser.add_argument("-j", "--job", action="store_true")
parser.add_argument("--other", action="store_true")
# parser.add_argument("--last", action="store_true")
parser.add_argument("--unshuffled", action="store_true")
parser.add_argument("-f","--field-aware", action="store_true")
args = parser.parse_args()

# not implemented
if args.other :
    print("[ERROR] --other is not implemented")
    exit(1)
    
# if args.last :
#     print("[ERROR] --last is not implemented")
#     exit(1)

# read args
output  = args.output
dataset = args.dataset
itemfile  = os.path.join(dataset,"u.item.utf8")
userfile  = os.path.join(dataset,"u.user")
occupationfile = os.path.join(dataset,"u.occupation")

# create output directory
if not os.path.exists(output):
    os.makedirs(output)
    

# input data description
name = [ "u1", "u2", "u3", "u4", "u5" ]
ext_train = ".base"
ext_test  = ".test"

# read item file
movie_to_genre_vector = {}
for line in open(itemfile,"r"):
    line = line.rstrip("\n").split("|")
    movie = line[0]
    movie_to_genre_vector[movie] = np.array(line[5:],dtype=int)
# read occupation file
occupation_to_number = { occ:i for (i,occ) in enumerate(open(occupationfile,"r").read().split()) }
# read user file
id_to_userinfo = {} # ( age, gender, occupation_number )
for line in open(userfile,"r"):
    line = line.rstrip("\n").split("|")
    id = line[0]
    id_to_userinfo[id] = (line[1],line[2],occupation_to_number[line[3]])

def get_field( field ):
    if args.field_aware:
        return str(field)+":"
    else:
        return ""

def emit_libfm( infile, outfile, train_db ):
    with open(outfile,"w") as out:
        lines = []
        for line in open(infile):
            lines += [line]
        # shuffle
        if not args.unshuffled:
            random.shuffle(lines)
        # generate
        for line in lines:
            offset = 0
            field = 0
            line = line.rstrip("\n").split("\t")
            id, movie, rate, time = line
            # rate
            out.write(rate)
            # user id
            if True:
                out.write(" "+get_field(field)+str(offset+int(id))+":1")
                offset += len(id_to_userinfo)
                field += 1
            # movie id
            if True:
                out.write(" "+get_field(field)+str(offset+int(movie))+":1")
                offset += len(movie_to_genre_vector)
                field += 1
            # timespamp
            if args.timestamp:
                out.write(" "+get_field(field)+str(offset)+":"+time)
                offset += 1
                field += 1
            # genre
            if args.genre:
                for i,val in enumerate(movie_to_genre_vector[movie]):
                    if val == 1:
                        out.write(" "+get_field(field)+str(offset+i)+":1")
                offset += len(movie_to_genre_vector[movie])
                field += 1
            # age
            if args.age:
                age, _, _ = id_to_userinfo[id]
                out.write(" "+get_field(field)+str(offset)+":"+age)
                offset += 1
                field += 1
            # sex
            if args.sex:
                _, gender, _ = id_to_userinfo[id]
                if   gender == "M":
                    out.write(" "+get_field(field)+str(offset)+":1 ")
                elif gender == "F":
                    out.write(" "+get_field(field)+str(offset+1)+":1 ")
                offset += 2
                field += 1
            # occupation
            if args.job:
                _, _, num_occupation = id_to_userinfo[id]
                out.write(" "+get_field(field)+str(offset+num_occupation)+":1")
                offset += len(occupation_to_number)
                field += 1
            out.write("\n")
            
def convert_to_libfm( infile_train, infile_test, outfile_train, outfile_test ):
    # create empty lists
    train_lines = []

    # read infile_train
    for line in open(infile_train):
        train_lines += [line]
        
    # create database from train_lines
    train_db = { id:set() for (id,_) in id_to_userinfo.items() }
    for line in train_lines:
        line = line.rstrip("\n").split("\t")
        id, movie, rate, timestamp = line
        train_db[id].add((movie,rate,timestamp))

    emit_libfm( infile_train, outfile_train, train_db )
    emit_libfm( infile_test,  outfile_test,  train_db )
    
# create libfm dataset
for u in name:
    convert_to_libfm( os.path.join(dataset,u+ext_train),
                      os.path.join(dataset,u+ext_test),
                      os.path.join(output,args.prefix_train+u+".txt"),
                      os.path.join(output,args.prefix_test +u+".txt"))
