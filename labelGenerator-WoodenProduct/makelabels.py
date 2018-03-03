#!/usr/bin/env python3

from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import csv
import re
import sys

#finding longest common substring in an array for tile name in each label
def longSubstr(data):
    substr = ''
    if len(data) > 1 and len(data[0]) > 0:
        for i in range(len(data[0])):
            for j in range (len(data[0])-i+1):
                if j > len(substr) and all(data[0][i:i+j] in x for x in data):
                    substr = data[0][i:i+j]
    return substr

# group like colors in lists
def groupPlanks(planks):
    groupedPlanks = []
    color = []
    count = 0
    for plank in planks:
        count += 1
        if count <= len(planks): #if we're not on last record in array
            if not color: # if list empty
                color.append(plank)
            else:
                # check if plank is the same color as what is in the color list
                if plank[2].split()[1] == color[0][2].split()[1] :
                    color.append(plank)
                else:
                    groupedPlanks.append(color)
                    color = []
                    color.append(plank)
      
    groupedPlanks.append(color)
    count = 0

    
    return groupedPlanks

def getMaterial(desc):
    split = desc.split()
    desc = split.pop(0)
    desc += " " + split.pop(0)

    material = ""
    # adding " to engineered board thicknesses
    if len(split) == 2:
        material += split.pop(0) + '" '
    material += split.pop()

    return material, desc

##START OF THE PROGRAM
if len(sys.argv) == 1:
    print("please pass an item list in CSV format")
    sys.exit()

itemlist = sys.argv[1]
f = open(itemlist)
r = csv.reader(f)
filter = input("filter by: ")

descs = []
planks = []

# search for size, remove size, sort the tile line by color

for row in r:
    priceRaw = row[3]
    price = priceRaw.lstrip("$")
    plank = [] # [code, size, description]
    code = row[0]
    desc = row[1]
    if filter.lower() in desc.lower():
        size = re.search(r'(\d{1})(\-*)(\d{0,1})(\/*)(\d{0,2})(\+*)(\d{0,1})(\-*)(\d{0,1})(\/*)(\d{0,2})', desc)
        if size:
            # remove size from description
            desc = desc.replace(size.group(), '')
            size = size.group() + '"' # extract match from obj
        else:
            size = "None"

        # remove material from desc
        material, desc = getMaterial(desc)

        # now that we added a size place holder, we can sort by color
        plank.append(code)
        plank.append(size)
        plank.append(desc)
        plank.append(material)
        plank.append(price)
        planks.append(plank)

f.close()

# # sort the list by color
planks.sort(key=lambda s: s[2].split()[1])

# sending array for grouping same lines into seperate arrays
groupedPlanks = groupPlanks(planks)

doc = SimpleDocTemplate(filter+".pdf", topMargin=0.24 * inch, bottomMargin=0, pagesize=letter)
logo = Image("logo.png")
logo.drawHeight = 0.25*inch
logo.drawWidth = 1.5*inch
width, height = letter
pos = 0
data = []
pair = []
names = []

styles = getSampleStyleSheet()

#cell formating
for j in range (len(groupedPlanks)):
    item = groupedPlanks[j]
if item:
    for i in range(len(groupedPlanks)):
            #extracting the name of the tile
            #if there are more than one item with the same name, we will look for the longest common string for the name
            if len(groupedPlanks[i]) > 1:
                for j in range(len(groupedPlanks[i])):
                    names.append(groupedPlanks[i][j][2])
                    plankName = longSubstr(names)
            else:
                plankName = groupedPlanks[i][0][2]

            if len(groupedPlanks[i]) > 8: #ammend font size if too many sizes per label
                fs = 7
            else:
                fs = 10

            pair.append([logo,Paragraph('''<para align=center><b> '''+plankName+'''</b><br></br>'''
                                    +'<br></br>'.join(['<b>'+groupedPlanks[i][x][1] +' ' + groupedPlanks[i][x][3] + ' $'
                                                       + groupedPlanks[i][x][4] + '/sqft</b>' for x in range(len(groupedPlanks[i]))])+'''</para> ''',
                                    ParagraphStyle(name='Normal',
                                                   fontName='Times-Roman',
                                                   fontSize=fs))])
            names = []
            if len(pair) % 2 == 0:
                data.append(pair)
                pair = []
            
            if groupedPlanks[i] == groupedPlanks[-1]:
                if len(pair) % 2 != 0:
                    pair.append([logo,Paragraph('''<para align=center><b> '''+'EMPTY'+'''</b><br></br>'''
                                                +'<br></br>'.join(['<b>'+'99"x99"'+'</b>   '+'99-999'+'   '+'<b>$'
                                                                    +"3.99"+'/sqft</b>' ])+'''</para> ''',
                                                ParagraphStyle(name='Normal',
                                                                fontName='Times-Roman',
                                                                fontSize=fs))])
                    data.append(pair)
                    pair = []


# table formatting and style
table = Table(data, colWidths=width/2, rowHeights=149)
table.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                           ('VALIGN',(0,0),(-1,-1),'CENTRE'),
                           ('BOX', (0,0), (-1,-1), 0.25, colors.white),
                           ('INNERGRID', (0,0), (-1,-1), 0.25, colors.white)]))

doc.build([table])

