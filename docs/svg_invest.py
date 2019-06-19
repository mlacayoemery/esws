import svgwrite

#https://stackoverflow.com/questions/17127083/python-svgwrite-and-font-styles-sizes
def invest_model(path,
                 profile,
                 title,
                 inputs,
                 outputs):

    dwg = svgwrite.Drawing(path, profile=profile)
    

    g = dwg.g(style="font-size:30;font-family:Comic Sans MS, Arial;"
              "font-weight:bold;font-style:oblique;stroke:black;"
              "stroke-width:1;fill:none")

    g.add(dwg.text("your text", insert=(10,30))) # settings are valid for all text added to 'g'
    dwg.add(g)
      
    dwg.save()

if __name__ == "__main__":
    invest_model('test.svg',
                 'tiny',
                 "Water Yield",
                 [],
                 [])
