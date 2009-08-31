/*
 * Created on 10-Nov-2004
 * Copyright 2004 by Ciaran Jessup, ciaranj@gmail.com
 * 
 * Portions Copyright 2000 by Peter Thoeny, Peter@Thoeny.com.
 * It is hereby granted that this software can be used, copied, 
 * modified, and distributed without fee provided that this 
 * copyright notice appears in all copies.
 * Portions Copyright (C) 2001 Motorola - All Rights Reserved
 */
package com.wombatinvasion.pmwikidraw;

import java.awt.Cursor;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Image;
import java.awt.Rectangle;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLConnection;
import java.net.UnknownServiceException;
import java.util.HashMap;
import java.util.HashSet;

import javax.swing.JApplet;
import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JPasswordField;

import org.jhotdraw.framework.Drawing;
import org.jhotdraw.framework.Figure;
import org.jhotdraw.framework.FigureEnumeration;
import org.jhotdraw.util.Storable;
import org.jhotdraw.util.StorableOutput;




/**
 * @author bob
 *
 * TODO To change the template for this generated type comment go to
 * Window - Preferences - Java - Code Style - Code Templates
 */
public class PmWikiDraw extends JApplet implements PmWikiSource {
	
	private PmWikiDrawFrame app = null;
	private static String fResourcePath;
	
	private String currentUploadPassword = "";
	
	public static final String VERSION ="2.362";
	
	private HashMap  modifiedParameters = new HashMap();
	
	/* (non-Javadoc)
	 * @see java.applet.Applet#init()
	 */
	public void init() {
		super.init();
		System.out.println("PmWikiDraw v"+VERSION);
		fResourcePath = getParameter(PmWikiSource.PARAMETER_RESOURCESURL);
		app = new PmWikiDrawFrame(this);
		app.open();
		
/*		//For some reason Java5 appears to need to have this to ask for authentication when running
		//as a standalone applet *sigh*
*/		
		/* Authenticator.setDefault(new DialogAuthenticator()); */
		app.loadDrawing(PmWikiSource.PARAMETER_DRAWINGLOADPATH);
	}
	/* (non-Javadoc)
   * @see com.wombatinvasion.pmwikidraw.PmWikiSource#getParameter(java.lang.String)
   */
  public String getPmWikiParameter(String parameter)
  {
  	if(modifiedParameters.containsKey(parameter)) {
  		return (String) modifiedParameters.get(parameter);
  	}
  	else {
  		return getParameter(parameter);
  	}
  }
  
  public void setPmWikiParameter(String parameter, String value) {
  	modifiedParameters.put(parameter, value);
  }
  
  /* (non-Javadoc)
   * @see com.wombatinvasion.pmwikidraw.PmWikiSource#createUrl(java.lang.String)
   */
  public URL createUrl(String filename) throws MalformedURLException
  {
      return new URL(getCodeBase(), filename);
  }
  
  public void debug(String string) {
    System.err.println(string);
  }
  
  public int saveDrawing(Drawing drawing) {
    int savedDraw;
    savedDraw = PmWikiSource.SAVE_FAILURE_PASSWORD;

    // set wait cursor
    setCursor(new Cursor(Cursor.WAIT_CURSOR));
    String drawingContent = null;
    String imageContent = null;
    String mapContent = null;

    try
    {
      // saves the drawing to the stream of bytes
      ByteArrayOutputStream out = new ByteArrayOutputStream();
      StorableOutput output = new StorableOutput(out);
      // drawing() (class DrawFrame) returns the Drawing element
      // Drawing is a StandardDrawing (extends Drawing
      // and implements CompositeFigures)
      
      output.writeStorable((Storable)drawing);
      output.close();

      String wikiUrl = getPmWikiParameter(PmWikiSource.PARAMETER_WIKIURL);

      // gets pathname of the drawing
      String drawingName = getPmWikiParameter(PmWikiSource.PARAMETER_DRAWING);
      if (drawingName == null)
        drawingName = "untitled";

      // gets script name
      String pageName = getPmWikiParameter(PmWikiSource.PARAMETER_PAGENAME);
      debug("PageName:" + pageName);
      showStatus("Page : " + pageName);
      if (pageName == null)
        pageName = "";

      // submit POST command to the server three times:
      // *.draw, *.map and *.gif
      // first upload *.draw file
      showStatus("Saving .draw file " + drawingName+".draw");
      debug("Saving .draw file " + drawingName+".draw");
      drawingContent = out.toString();

      int iBorder = 10;
      Dimension d = new Dimension(0, 0); // not this.view().getSize();

      // calculate the minimum size of the gif image
      FigureEnumeration k = drawing.figuresReverse();
      while (k.hasNextFigure())
      {
        Figure figure = k.nextFigure();
        Rectangle r = figure.displayBox();
        if (r.x + r.width > d.width)
        {
          d.setSize(r.x + r.width, d.height);
        }
        if (r.y + r.height > d.height)
        {
          d.setSize(d.width, r.y + r.height);
        }
      }
	      String map = drawing.getMap();
	      String mapPath = drawingName + ".map";
	      showStatus("Saving .map file " + mapPath);
	      // enclose the map and add editable border. Note that the
	      // edit border is added LAST so the earlier AREAs take
	      // precedence.
	      String area = "<area shape=\"rect\" coords=\"";
	      String link = "\" href=\"$editImageUrl\" " + "alt=\"Click to edit the image\" title=\"Click to edit the image\"  />\n";
	      map = "<map name=\"" + drawingName + "\" id=\""+ drawingName +" \">" + map + 
	
	      area +
		    "0,0," + (d.width+iBorder) + "," + (iBorder/2) +
		    link +
	
		    area +
		    "0,0," + iBorder/2 + "," + (d.height+iBorder) +
		    link +
	
		    area +
		    (d.width+iBorder/2) + ",0," + (d.width+iBorder) + "," +
	          (d.height+iBorder) +
		    link + 
	
		    area +
		    "0," + (d.height+iBorder/2) + "," +
		    (d.width+iBorder) + "," + (d.height+iBorder) +
		    link +
	
		    "</map>";
	      mapContent = map;
      	  
		      // gets pathname of the GIF image
		      String gifPath  = drawingName + ".gif";
		
		      // then create *.gif image and upload file
		      showStatus("Saving .gif file " + gifPath);

				  final Image oImgBuffer = app.createImage(d.width + iBorder,d.height + iBorder);
		      final char[] aChar = app.convertToGif(oImgBuffer);

		      imageContent = String.valueOf(aChar, 0, aChar.length);
		      String postResult = post(wikiUrl, drawingName, pageName,imageContent, drawingContent, mapContent);
		      if(postResult.equals("SUCCESS")) {
		      	savedDraw = PmWikiSource.SAVE_SUCCESS;
		      }
		      else if(postResult.equals("FAILURE")){  
		      	// Need to improve this, currently its a guess.
		      	savedDraw = PmWikiSource.SAVE_FAILURE_PASSWORD;
		      	showStatus("Your Password(probably) was incorrect.");
		      } 
		      else { 
		      	// Update with our new basetime.
		      	showStatus("Concurrent modification to drawing.");
		      	savedDraw = PmWikiSource.SAVE_FAILURE_CONCURRENTMODIFICATION;
		      }
	    } catch (MalformedURLException e)
	    {
	      this.setCursor(new Cursor(Cursor.DEFAULT_CURSOR));
	      showStatus("Bad Wiki servlet URL: " + e.getMessage());
	    } catch (IOException e)
	    {
	      e.printStackTrace();
	      this.setCursor(new Cursor(Cursor.DEFAULT_CURSOR));
	      showStatus(e.toString());
	    }
    this.setCursor(new Cursor(Cursor.DEFAULT_CURSOR));
//    showStatus("Saved .draw " + (savedDraw == 1 ? "OK" : "Failed") + " .map "
  //      + (savedMap == 1 ? "OK" : "Failed") + " .gif "
    //    + (savedGif == 1 ? "OK" : "Failed")  
		//+ (savedDraw == 2 ? " Password Incorrect!" : "") 
	//);
    return savedDraw;    
  }
  
  /* Bad me, should use a char array or something else */
	static String password = "";

  
  /**
   * x Submits POST command to the server, and reads the reply.
   * @return "SUCCESS" on success
   * @return "FAIL" on password failure
   * @return a new timestamp if failed due to concurrent modifications :)
   */
	
	public String post(String url, String drawingName, String pageName,
      String imageContent, String drawingContent, String mapContent) throws MalformedURLException, IOException
  {
  	int tryCount = 0;
  	boolean askForPassword = false;
  	boolean concurrentModification = false;

    String drawingBaseTime = getPmWikiParameter(PARAMETER_DRAWINGBASETIME);
    System.out.println("Current drawing baseTime:" + drawingBaseTime);
    
  	String newTimeStamp = "";
    String sep = "89692781418184";
    while (imageContent.indexOf(sep) != -1)
      sep += "x";

    while (drawingContent.indexOf(sep) != -1)
      sep += "x";
    
    while (mapContent.indexOf(sep) != -1)
      sep += "x";
    String message = makeMimeForm(pageName, drawingName, imageContent,  drawingContent, mapContent, sep, password, drawingBaseTime);

  	while(tryCount<3) {
  		askForPassword = false;
	
	    URL server = new URL(url);
	    debug("Actual URL:" + server.toString());
	    URLConnection connection = server.openConnection();
	
	    connection.setAllowUserInteraction(true);
	    connection.setDoOutput(true);
	    connection.setUseCaches(false);
	
	    connection.setRequestProperty("Content-type", "multipart/form-data; boundary=" + sep);
	    connection.setRequestProperty("Content-length", Integer.toString(message.length()));
	    if (getParameter("debug") != null)
	    {
	      debug(message);
	    }
	
	    String replyString = null;
	    try
	    {
	      DataOutputStream out = new DataOutputStream(connection.getOutputStream());
	      out.writeBytes(message);
	      out.close();
	      debug("Wrote " + message.length() + " bytes to\n" + connection);
	
	      try
	      {
//	        for(int i=0;i<connection.getHeaderFields().size();i++) {
	//        	System.err.println("REPLY(Headers): "+connection.getHeaderFieldKey(i)+":"+connection.getHeaderField(i));	
	  //      }
	        if(connection.getHeaderField("PmWikiDraw-DrawingChanged")!= null) {
	        	// This will be returned from PmWiki if a concurrent modification has occurred *sigh* Damn those other people! ;)
	        	
            newTimeStamp = connection.getHeaderField("PmWikiDraw-DrawingChanged");
	        	concurrentModification = true;
            setPmWikiParameter(PARAMETER_DRAWINGBASETIME, newTimeStamp);
	        }

          if(connection.getHeaderField("PmWikiDraw-DrawingBaseTime")!= null) {
            // This will be returned from PmWiki always, used to allow for multiple saves within a single session.
            
            newTimeStamp = connection.getHeaderField("PmWikiDraw-DrawingBaseTime");
            setPmWikiParameter(PARAMETER_DRAWINGBASETIME, newTimeStamp);
          }	        
	        if(!concurrentModification) {
		      	BufferedReader in = new BufferedReader(new InputStreamReader(connection.getInputStream()));
		        String reply = null;
		        while ((reply = in.readLine()) != null)
		        {
		          if(getPmWikiParameter(PARAMETER_DEBUG) != null) {
		            System.err.println("REPLY:"+reply);
		          }
		        	if(reply.indexOf("name='authpw'") > -1) {
		        		askForPassword = true;
		        	}
		          if (reply.startsWith("ERROR "))
		          {
		            replyString = reply.substring("ERROR ".length());
		          }
		        }
		        in.close();
	        }
	      } catch (IOException ioe)
	      {
	        replyString = ioe.toString();
	      }
	    } catch (UnknownServiceException use)
	    {
	      replyString = use.getMessage();
	      debug(replyString);
	    }
	    if(askForPassword) {
	    	password =  getPopupPassword(tryCount);
	    	message = makeMimeForm(pageName, drawingName, imageContent,  drawingContent, mapContent, sep, password, drawingBaseTime);
	    } 
	    else if(concurrentModification) {
	    	tryCount = 6; // Force exit
	    }
	    else {
	    	return "SUCCESS";
	    }
	    tryCount++;
  	}
  	if(askForPassword) {
  		return "FAILURE";
  	}else if(concurrentModification)
  		return "CONCURRENT_MODIFICATION";
  	else {
  		return "SUCCESS";
  	}
  }
	
  //-----------------------------------------------------------------------

  /**
   * create name="value" MIME form data like:
   *   -----------------------------1234567
   *   Content-Disposition: form-data; name="theName"
   *   
   *   theValue
   */

  /**
   * create name="value" file MIME form data like:
   *   -----------------------------1234567
   *   Content-Disposition: form-data; name="theName"; filename="theValue"
   *   
   *   theContent
   */

  static String NL = "\r\n";
  static String NLNL = NL + NL;

  /** Post the given message */
  private String makeMimeForm(
String pageName,
String drawingName,
String imageContent,
String drawingContent,
String mapContent,
String sep, 
String password,
String drawingBaseTime) {

String mime_sep = NL + "--" + sep + NL;
return
    "--" + sep + "\r\n" 
				+ "Content-Disposition: form-data; name=\"pagename\"" + NLNL
				+ pageName
    + mime_sep
    			+ "Content-Disposition: form-data; name=\"authpw\"" + NLNL
				+ password
	+ mime_sep
    			+ "Content-Disposition: form-data; name=\"drawingname\"" + NLNL
				+ drawingName
    + mime_sep
          		+ "Content-Disposition: form-data; name=\"action\"" + NLNL
				+ "postDrawing"
    + mime_sep
    			+ "Content-Disposition: form-data; name=\"noredirect\"" + NLNL //For PmWiki1
    			+ "fish"
    + mime_sep
   				+ "Content-Disposition: form-data; name=\"redirect\"" + NLNL // For PmWiki2 
   				+ "0"
   	+ mime_sep
   				+ "Content-Disposition: form-data; name=\"drawingbasetime\"" + NLNL  
   				+ drawingBaseTime
   	+ mime_sep
    			+ "Content-Disposition: form-data; name=\"uploadDrawing\"; "
    			+ "filename=\"" + drawingName + ".draw\"" + NL
    			+ "Content-Type: text/plain" + NL
    			+ NL
    			+ drawingContent
    + mime_sep
    			+ "Content-Disposition: form-data; name=\"uploadMap\"; "
    			+ "filename=\"" + drawingName + ".map\"" + NL
    			+ "Content-Type: text/plain" + NL
    			+ NL
    			+ mapContent
    + mime_sep 
          + "Content-Disposition: form-data; name=\"uploadImage\"; "
          + "filename=\"" + drawingName + ".gif\"" + NL
          + "Content-Type: image/gif" + NL
          + "Content-Transfer-Encoding: binary" + NL
          + NL
          + imageContent
    + mime_sep
    + NL + "--" + sep + "--" + NL;
  }
  

  
  /** Replace current app with a different URL */
	void exitApplet(boolean saved)
	{
		String viewPath = getParameter(PmWikiSource.PARAMETER_WIKIURL) 
		+ "?pagename="+getParameter(PmWikiSource.PARAMETER_PAGENAME);
		if(saved) {
//			viewPath += "&action=postEditImage&image="+getParameter(PmWikiSource.PARAMETER_DRAWING);
		}
	  
	  if (viewPath != null)
	  {
	    try
	    {
	      URL url = new URL(viewPath);
	      if(getParameter(PmWikiSource.PARAMETER_DEBUG) == "true") {
	      	System.out.println("Redirecting page to: "+viewPath);
	      }
	      getAppletContext().showDocument(url);
	    } catch (MalformedURLException mue)
	    {
	      showStatus("Bad URL for viewpath " + viewPath);
	    }
	  }
	}

	public void exit(boolean saved) {
	  exitApplet(saved);
	}
	
	public String getPopupPassword(int tryCount) {
		final JDialog passwordDlg = new JDialog();
		JPasswordField passwordField = new JPasswordField(15);
		JButton okButton = new JButton("OK!");
		okButton.addActionListener(new ActionListener() {
			/* (non-Javadoc)
			 * @see java.awt.event.ActionListener#actionPerformed(java.awt.event.ActionEvent)
			 */
			public void actionPerformed(ActionEvent arg0) {
				passwordDlg.hide();
			}
		});
		passwordDlg.setTitle("PmWiki Upload password (Attempt "+(tryCount+1)+")");
		passwordDlg.getContentPane().setLayout(new FlowLayout());
		passwordDlg.getContentPane().add(new JLabel("Password :"));
		passwordDlg.getContentPane().add(passwordField);
		passwordDlg.getContentPane().add(okButton);
		passwordDlg.setModal(true);
		passwordDlg.pack();
		passwordDlg.setVisible(true);
		return passwordField.getText();
	}
	
	/**
	 * *Sigh* Really really horrible way to get the current resource path
	 * into the ImagFigure when it loads :( Any better ideas?
	 * @return
	 */
	public static String getResourcePath() {
		return fResourcePath;
	}
}
