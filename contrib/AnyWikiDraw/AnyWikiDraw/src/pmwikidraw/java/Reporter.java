import qdxml.DocHandler;
import qdxml.QDParser;

import java.util.Hashtable;
import java.util.Enumeration;

import java.io.FileReader;

/** 
  This class is the most basic possible
  implementation of the DocHandler class.
  It simply reports all events to System.out
  as they occur.
*/
public class Reporter implements DocHandler {

  // We only instantiate one copy of the DocHandler
  static Reporter reporter = new Reporter();

  // Implementation of DocHandler is below this line
  public void startDocument() {
    System.out.println("  start document");
  }
  public void endDocument() {
    System.out.println("  end document");
  }
  public void startElement(String elem,Hashtable h) {
    System.out.println("    start elem: "+elem);
    Enumeration e = h.keys();
    while(e.hasMoreElements()) {
      String key = (String)e.nextElement();
      String val = (String)h.get(key);
      System.out.println("      "+key+" = "+val);
    }
  }
  public void endElement(String elem) {
    System.out.println("    end elem: "+elem);
  }
  public void text(String text) {
    System.out.println("        text: "+text);
  }
  // implementation of DocHandler is above this line

  /** Usage: java Reporter [xml file(s)] */
  public static void main(String[] args) throws Exception {
    for(int i=0;i<args.length;i++)
      reportOnFile(args[0]);
  }

  public static void reportOnFile(String file) throws Exception {
    System.out.println("===============================");
    System.out.println("file: "+file);

    // This is all the code we need to parse
    // a document with our DocHandler.
    FileReader fr = new FileReader(file);
    QDParser.parse(reporter,fr);

    fr.close();
  }
}
