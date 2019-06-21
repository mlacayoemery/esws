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

def connector_table(insert=(0,0),
                    unit=1):

    t="M0,0"\
       " l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i"\
       " l%i,0 l%i,0 l%i,0 l%i,0 l%i,0"\
       " l0,%i l0,%i"\
       " l%i,0"\
       " l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i"\
       " l-%i,0"\
       " l0,%i l0,%i"\
       " l-%i,0 l-%i,0 l-%i,0 l-%i,0 l-%i,0"\
       " l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i"
    p = t % tuple([unit]*t.count("%i"))

    print(p)

    return svgwrite.path.Path(d=p,
             fill="none", 
             stroke="#000000", stroke_width=unit/40.0)


def connector_raster(insert=(0,0),
                    unit=1):

    t="M0,0"\
       " l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i"\
       " l%i,0 l%i,0 l%i,0"\
       " l0,%i l0,%i"\
       " l%i,0 l%i,0 l%i,0 l%i,0 l%i,0"\
       " l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i"\
       " l-%i,0 l-%i,0 l-%i,0 l-%i,0 l-%i,0"\
       " l0,%i l0,%i"\
       " l-%i,0 l-%i,0 l-%i,0"\
       " l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i"
    p = t % tuple([unit]*t.count("%i"))

    print(p)

    return svgwrite.path.Path(d=p,
             fill="none", 
             stroke="#000000", stroke_width=unit/40.0)
    
    
def connector_vector(insert=(0,0),
                     unit=1):

    z = float(unit)
    dx = (z * 0.5) * (3**0.5)    
    dy = z * 0.5

    p=""
    
    t="M0,0 l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i l%i,0 l%i,0 l%i,0 l0,%i"
    p = p + (t % tuple([unit]*t.count("%i")))

    t=" l%f,%f l%f,%f l%f,%f l%f,-%f l%f,-%f l%f,-%f"
    p = p + (t % tuple([dx, dy]*int(t.count("%f")/2)))

    t=" l0,-%i l0,-%i l0,-%i"
    p = p + (t % tuple([unit]*t.count("%i")))

    t=" l-%f,-%f l-%f,-%f l-%f,-%f l-%f,%f l-%f,%f l-%f,%f"
    p = p + (t % tuple([dx, dy]*int(t.count("%f")/2)))

    t=" l0,%i l-%i,0 l-%i,0 l-%i,0 l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i"
    p = p + (t % tuple([unit]*t.count("%i")))   

    print(p)

    return svgwrite.path.Path(d=p,
             fill="none", 
             stroke="#000000", stroke_width=unit/40.0)


if __name__ == "__main__":

    path = "test.svg"
    profile = "tiny"

    dwg = svgwrite.Drawing(path, profile=profile)

    #dwg.add(dwg.text("your text", insert=(10,30)))

    #dwg.add(connector_table())
    #dwg.add(connector_raster())    
    dwg.add(connector_vector())

    dwg.save()

##    invest_model('test.svg',
##                 'tiny',
##                 "Water Yield",
##                 [],
##                 [])
