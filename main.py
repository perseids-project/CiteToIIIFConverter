'''
Created on May 9, 2016

@author: elijah cooke
'''
import sys, os;
import json;
import ujson;
import collections;

try:
    from lxml import etree
    print("running with lxml.etree")
except ImportError:
    try:
        import xml.etree.cElementTree as etree  
        print("running with cElementTree on Python 2.5+")
    except ImportError:
        try:
            # Python 2.5
            import xml.etree.ElementTree as etree
            print("running with ElementTree on Python 2.5+")
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as etree
                print("running with cElementTree")
            except ImportError:
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as etree
                    print("running with ElementTree")
                except ImportError:
                    print("Failed to import ElementTree from any known place")

def converttoiiif(file):
    #takes in the base url from the console (will need to be updated with the way to get url from persieds)
    baseurl = input("enter base url for manifest: ")
    imagebaseurl = input("enter base url for images: ")
    #takes in the largest height and width of images to be included in this file
    height = input("enter the height of the tallest image referenced by this file: ")
    width = input("enter the width of the widest image referenced by this file: ")
    parser = etree.XMLParser(remove_pis=True)
    #builds the xml file into a tree
    tree = etree.parse(file,parser)
    root = tree.getroot()
    ns = {"xml":"http://www.tei-c.org/ns/1.0"}
    metadata = []
    #goes through all the metadata in the xml file and enters it into the list of dictionarys to be added to the json manifest
    for ele in root.find(".//xml:fileDesc", namespaces = ns).iter():
        if ele.text:
            metadata.append({"label":etree.QName(ele.tag).localname,"value":ele.text})
    #takes the title and pairs it down to the cts namespace and the work identifier
    title = root.find(".//xml:title",namespaces = ns)
    label = title.text.replace("urn:cts:","")
    #creates and ordered dict to store the words as we look to see how many unique images are ref in the xml file
    pages = collections.OrderedDict() 
    #iterates over every word and and check if the image is in the dictionary.
    #if it is it adds the word into the list of words that are stored as tuples.
    #if it is not it creates a key for the images with list of the words stored astuples 
    for n in root.findall(".//xml:w", namespaces = ns):
        objid, wordid = n.get("facs").split(":",3)[3].split("@",1)
        if objid in pages:
            data = [wordid,n.text,objid]
            pages[objid].append(data)
        else:
            pages[objid] = [[wordid,n.text,objid]]
    num = 0
    # reads through each images and creates a canvas for it
    images=[]
    canvases=[]
    for x, y in pages.items():
        num = num + 1 
        resources = []
        # takes the list of words and creates the annotation list of words for the annotation file
        for z in y:
            cords = z[0].split('.')
            #creates the cordinates in format for IIIF
            fcords = cords[0]+","+cords[1]+","+cords[2]+","+cords[3]
            #takes each word 
            resources.append({
                              "@type":"oa:Annotation",
                              "motivation":"sc:painting",
                              "resource":{
                                          "@type":"cnt:ContentAsText",
                                          "chars":z[1],
                                          "format":"text/plain",
                                          },
                              "on":"http://"+baseurl+"/iiif/"+label+"/canvas/"+"p."+str(num)+"#xywh="+fcords
                              })
        #creates the annotation file           
        annolist = {
                    "@context":"http://iiif.io/api/presentation/2/context.json",
                    "@id":"http://"+baseurl+"/iiif/"+label+"/list/p."+str(num),
                    "@type":"sc:AnnotationList",
                    "resources":resources
                    } 
        annoout = json.dumps(annolist, sort_keys=True, indent=4, separators=(',',':'))
        annojson = open("p."+str(num)+".json","w")
        annojson.write(annoout)
        annojson.close   
        #need to add something to writ the annolist to a Json file here
        #creates the image in the IIIF file, currently the label height, width, and baseurl are placeholders until we see how the image are coming from persieds and how to get the info from them. All that will be need to done will be to put that into the var in the start of he function
        images.append({
                   "@type":"oa:Annotation",
                   "motivation":"sc:painting",
                   "resource":{
                               "@id":"http://"+imagebaseurl+"/iiif/"+z[2]+".jpg",
                               "@type":"dctypes:Image",
                               "format":"image/jpeg",
                               "height":height,
                               "width":width
                               },
                   "on":"http://"+baseurl+"/iiif/"+label+"/canvas/"+"p."+str(num)
                   })
        #creates the canvas for the image same things with images apply here
        canvases.append({
                     "@id":"http://"+baseurl+"/iiif/"+label+"/canvas/"+"p."+str(num),
                     "@type":"sc:Canvas",
                     "label":"p. "+str(num),
                     "height":height,
                     "width":width,
                     "images":images
                     })
    #creates a sequences with which the images should be displayed
    sequences = [{
                  "@id":"http://" + baseurl + "/iiif/" + label + "/sequence/normal",
                  "@type":"sc:Sequence",
                  "label":"Current Page Order",
                  "viewingDirection":"left-to-right",
                  "viewingHint":"paged",
                  "canvases":canvases,
                  }]
    #creates the manifest and enter the metadata captured earlier
    iiifjson = {
                "@context":"http://iiif.io/api/presentation/2/context.json",
                "@type":"sc:Manifest",
                "@id":"http://" + baseurl + "/iiif/book1/manifest",
                
                "label":label,
                "metadata":metadata,
                "sequences":sequences
                }
    return iiifjson;
def main():
    #takes in a file as an argument and converts this annotations to IIIF
    file_to_convert = sys.argv[1]
    iiifdoc = converttoiiif(file_to_convert)
    # writes the IIIF data to a Json file. 
    data = ujson.dumps(iiifdoc, sort_keys=True, indent=4, escape_forward_slashes=True)
    file = open("manifest.json","w")
    file.write(data)
    file.close
main()
