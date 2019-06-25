import svgwrite
import math

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


def eliptical_arc(start_x=0,
                  start_y=0,
                  stop_y=1,
                  radius=1,
                  start_deg=0,
                  stop_deg=180):
   
    degree0 = start_deg
    degree1 = stop_deg
    radians0 = math.radians(degree0)
    radians1 = math.radians(degree1)
    dx0 = radius*(math.sin(radians0))
    dy0 = radius*(math.cos(radians0))
    dx1 = radius*(math.sin(radians1))
    dy1 = radius*(math.cos(radians1))

    m0 = dy0 
    n0 = -dx0 
    m1 = -dy0 + dy1 
    n1 = dx0 - dx1 

    p = ""
    if start_x is None or start_y is None:
        p = " m0,0"
    else:
        p = " M%f,%f" % (start_x, start_y)
        
    p = p + "M %f,%f" % (m0, n0)
    
    p = p + "a %f,%f 0 0,0 %f,%f" % (radius, radius, m1, n1)

    #p = p + " z"

    print(p)

    return svgwrite.path.Path(d=p,
             fill="none", 
             stroke="#000000", stroke_width=1/40.0)

def connector_misc(insert=(0,0),
                    unit=1):

##       " l0,%i l0,%i"\
##       " l%i,0"\
##       " l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i"\
##       " l-%i,0"\
##       " l0,%i l0,%i"\

    t="M0,0"\
       " l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i"\
       " l%i,0 l%i,0 l%i,0 l%i,0 l%i,0"

    #t = t + " a%f,%f 0 0,0 %f,%f" %  (n0, radius_c, m1, n1)

    #t = t + " a0.05,0.05 0 0,0 0,-1"
    t = t + " m0,-%i"

    t = t + " l-%i,0 l-%i,0 l-%i,0 l-%i,0 l-%i,0"\
       " l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i l0,-%i"
    p = t % tuple([unit]*t.count("%i"))


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
    #dwg.add(connector_vector())

    dwg.add(eliptical_arc(start_x=None,
                          start_y=None,
                          stop_y=1,
                          radius=1,
                          start_deg=0,
                          stop_deg=180))

    dwg.add(eliptical_arc(start_x=None,
                          start_y=None,
                          stop_y=1,
                          radius=1,
                          start_deg=180,
                          stop_deg=270))

    dwg.save()

##    invest_model('test.svg',
##                 'tiny',
##                 "Water Yield",
##                 [],
##                 [])
