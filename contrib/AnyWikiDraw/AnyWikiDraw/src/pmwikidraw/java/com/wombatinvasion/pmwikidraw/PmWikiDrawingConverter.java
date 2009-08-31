package com.wombatinvasion.pmwikidraw;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.StringTokenizer;

import org.jhotdraw.framework.FigureAttributeConstant;


/**
 * <p>Title: </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2004</p>
 * <p>Company: Smart Analytics</p>
 * @author Ciaran Jessup
 * @version 1.0
 */

/*
 *  Modified:
 *   06-Dec-2004	cj       Initial development
 */

//------------------------------------------------------------------------------
/**
 * PmWikiDrawingConverter
 */
public class PmWikiDrawingConverter
{

  List lines = new ArrayList();
  
  public void convert(InputStream in) throws IOException {
    BufferedReader reader = new BufferedReader(new InputStreamReader(in));
    int linecount = 0;
    lines.clear();
    String line;
    while ((line = reader.readLine()) != null){
//        System.out.println((linecount++)+"< "+line);
        lines.add(line);
    }
    if(lines.size() >1) {
      // Check/Fix drawingtype [Note only needs to be done for pre PmWikiDrawing types normal rules apply after then.
      String drawingType = (String) lines.get(1);
      if( drawingType.indexOf("org.jhotdraw.standard.StandardDrawing")> -1 ) {
        // Old style drawing.
          int classOffset=  drawingType.indexOf("org.jhotdraw.standard.StandardDrawing");
          String elementCount = drawingType.substring(classOffset+"org.jhotdraw.standard.StandardDrawing".length(), drawingType.length()).trim();
          int currentNesting = nestingLevel(drawingType);
          String newDrawingType = buildNestingSegment(currentNesting)+"com.wombatinvasion.pmwikidraw.PmWikiDrawing"+" 0 "+elementCount; // Create new drawing type with version 0 so the conversion routines know this
          																																														 // is an archaic version.
          lines.set(1, newDrawingType);
      }
      
      int drawingVersion = getDrawingVersion();
	  if(drawingVersion != PmWikiDrawing.VERSION) {
	      if(drawingVersion > PmWikiDrawing.VERSION) {
	        System.err.println("Please upgrade this version of PmWikiDraw, you seem to have drawings that are more recent than I can handle :(!");
	      }
	      else {
	        System.out.println("Converting drawing with "+ lines.size()+ " lines.");
		      // Only need to convert drawings that are a differnt version.
		      switch(drawingVersion) {
		      	case 0:
		      	  System.err.println("Performing archaic upgrade.");
		      	  // This is a complex upgrade, there are 2 different forms, one with AttributeLineConnectors etc, and one without, so do the first type first and
		      	  // and then reprocess it as if it was the latter.
		      	  removeAttributeLinesandConnectors();
		      	  fixLineFiguresandConnectors();
		      	case 1: //Note the break is deliberately missing.
		      	  // Fix the TextFigure borders....
		      	  fixTextFigureBorders();
		      	  
		      	  
		      	default:
		      }
		      // Update the drawing version flag.
		      setDrawingVersion();
	      }
      }

	  // Do pre-processor type tasks that are always required, for example converting '%RESOURCE_URL%' to the *actual* current resource path.
//	  fixResourceReferences();
    }
    else { 
      //Do no conversion, weird format, can't do anything about!
    }
  }

  //------------------------------------------------------------------------------
  /**
   * 
   */
  private void fixTextFigureBorders()
  {
    for(int i=0;i<lines.size();i++) {
      String line = (String)lines.get(i);
      
      if(line.indexOf("org.jhotdraw.figures.TextFigure")>-1 ) {
        // Splice in "no attributes"
        	//String className = getClassName(i);
        	//int nestingLevel = nestingLevel(line);
        	//String attributes = line.substring(nestingLevel+ className.length()).trim();
        	
        	// Three cases, 1: No attributes defined....
        	//              2: Attributes defined...
        	//                -  Frame colour already defined.
        	//              3: Attributes defined...
        	//                -  Frame colour not defined.
        	if(line.indexOf(FigureAttributeConstant.FRAME_COLOR_STR)>-1) { //Case 2
        	  // Best case scenario, the frame colour is already defined.
        	  break;
        	}
        	else {
        	  if(line.indexOf("\"no_attributes\"")>-1) { // case 1
        	    // Reasonable case, just need to add a single attribute
        	    int index = line.indexOf("\"no_attributes\"");
        	    String before = line.substring(0, index);
        	    String after = line.substring(index+"\"no_attributes\"".length());
        	    //Create 2 attributes, FillColour + FrameColour both set to colour none.
        	    String middle = "\"attributes\" \"attributes\" 2 \"FrameColor\" \"Color\" 255 199 158 \"FillColor\" \"Color\" 255 199 158";
        	    lines.set(i, before + middle + after);
        	  }
        	  else { // Case 3..
        	    // Hard case need to calculate current number of attributes and add one.
        	    String result = line;
        	    int index = line.indexOf("\"attributes\"");
        	    int realIndex = index+ ("\"attributes\"".length()*2)+2; // Takes into account the fact that "attributes" is followed by "attributes" then the actual count.
        	    String before  = line.substring(0, realIndex); 
        	    
        	    String after = line.substring(realIndex);
        	    int nextElement = after.indexOf('"');
        	    String restOfLine = after.substring(nextElement);
        	    
        	    String strAttributeCount = after.substring(0, nextElement).trim();
        	    // Increment elementCount
        	    int intAttributeCount = Integer.parseInt(strAttributeCount);
        	    result = before + (intAttributeCount+1) + " \"FrameColor\" \"Color\" 255 199 158 "+ restOfLine;
        	    lines.set(i, result);
        	  }
        	}
      }
    }
  }

  private void fixLineFiguresandConnectors() {
    for(int i=0;i<lines.size();i++) {
      String line = (String)lines.get(i);
      
      if(line.indexOf("org.jhotdraw.figures.LineConnection")>-1 || 
          line.indexOf("org.jhotdraw.figures.LineFigure")>-1  ||
          line.indexOf("org.jhotdraw.figures.PolyLineFigure")>-1  ||
          line.indexOf("org.jhotdraw.figures.ElbowConnection")>-1 ) {
        // Splice in "no attributes"
        	
        	String className = getClassName(i);
        	int nestingLevel = nestingLevel(line);
        	String attributes = line.substring(nestingLevel+ className.length()).trim();
        	
        	String newLine =  line.substring(0, nestingLevel+className.length()) + " \"no_attributes\" " + attributes;
        	lines.set(i, newLine);
      }
    }
  }
private void removeAttributeLinesandConnectors() {
    boolean keepGoing = true;
    do {
      int i =0;
      for(i=0;i<lines.size();i++) {
        String line = (String)lines.get(i);
        if(line.indexOf("org.jhotdraw.contrib.AttributeConnectorFigure")>-1 || 
            line.indexOf("org.jhotdraw.contrib.AttributeLineFigure")>-1 ) {
          int nextObjectLine = findNextObjectLine(i, nestingLevel(line));
          if(nextObjectLine>=0) {
	          // Reduce the indent as removed the containing object.
	          for(int j=i+1;j<nextObjectLine;j++) {
	            reduceIndent(j);
	          }
          }
          
          lines.remove(i);
          fixReferences(i-1);
          break;
        }
      }
      if(i >= lines.size()) 
        keepGoing = false;
    }
    while(keepGoing == true);
  }
  
  public InputStream getConvertedStream() throws IOException {
    ByteArrayOutputStream baos = new ByteArrayOutputStream();
    BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(baos));
    
    Iterator it = lines.iterator();
    while(it.hasNext()) {
      String line = (String)it.next();
//      System.out.println("> "+line);
      writer.write(line);
    }
    writer.flush();
    writer.close();
    baos.flush();
    baos.close();
    
    ByteArrayInputStream bais = new ByteArrayInputStream(baos.toByteArray());
    return bais;
  }

  
  private int nestingLevel(String line) {
    for(int i=0;i<line.length();i++) {
      if(line.charAt(i)!=' ' && line.charAt(i)!='\t') {
        return i;
      }
    }
    /* Else  no whitespace found */
    return line.length();
  }
  
  private int findNextObjectLine(int currentLine, int currentNesting) {
    if(currentLine == lines.size()-1) {
      return -1;
    }
    else {
      for(int i=(currentLine+1); i<lines.size();i++) {
        if(nestingLevel((String)lines.get(i)) <= currentNesting) {
          return i;
        }
      }
      return lines.size()-1;
    }
  }
  
  public int getDrawingVersion() {
    String drawingType = (String) lines.get(1);
    int classOffset=  drawingType.indexOf("com.wombatinvasion.pmwikidraw.PmWikiDrawing");
    String attributes = drawingType.substring(classOffset+"com.wombatinvasion.pmwikidraw.PmWikiDrawing".length(), drawingType.length()).trim();
    int spaceChar = attributes.indexOf(' ');
    String drawingVersion = attributes.substring(0, spaceChar);
    String elementCount = attributes.substring(spaceChar+1, attributes.length());
    return Integer.parseInt(drawingVersion);
  }
  
  
  public void setDrawingVersion() {
    String drawingType = (String) lines.get(1);
    int classOffset=  drawingType.indexOf("com.wombatinvasion.pmwikidraw.PmWikiDrawing");
    int currentOffset = nestingLevel(drawingType); 
    String attributes = drawingType.substring(classOffset+"com.wombatinvasion.pmwikidraw.PmWikiDrawing".length(), drawingType.length()).trim();
    int spaceChar = attributes.indexOf(' ');
    String elementCount = attributes.substring(spaceChar).trim();
    String drawingVersion = ""+PmWikiDrawing.VERSION;
    lines.set(1, buildNestingSegment(currentOffset)+"com.wombatinvasion.pmwikidraw.PmWikiDrawing"+" "+ drawingVersion + " "+elementCount);
  }
  
  public String buildNestingSegment(int nestingLevel) {
    StringBuffer buffer = new StringBuffer();
    for(int i=0;i<nestingLevel;i++)
     buffer.append(" ");
    return buffer.toString();
  }
  
  public void reduceIndent(int line) {
    String sLine = (String)lines.get(line);
   if(nestingLevel(sLine)<=0) {
     System.err.println("Error condition, shouldn't be trying to reduceIndent, not possible!");
   }
   else {
    sLine = sLine.substring(4); // Strip off the four front characters.
     lines.set(line, sLine); 
   }
  }
  
  private String getClassName(int line) {
    String sLine = ((String)lines.get(line)).trim();
    int spacePos = sLine.indexOf(' ');
    sLine = sLine.substring(0, spacePos);
    return sLine;
  }
  
  private void fixReferences(int deletedReference) {
    for (int i=0;i<lines.size();i++) {
      String line = (String)lines.get(i);
      int refPos = line.indexOf("REF");
      if(refPos >-1) {
        String refValue = line.substring(refPos+4).trim();
        int iRefValue = Integer.parseInt(refValue);
        if(iRefValue > deletedReference) {
          iRefValue--;
        }
        String newLine = line.substring(0, refPos) + "REF "+ iRefValue;
        lines.set(i, newLine);
      }
    }
  }
}