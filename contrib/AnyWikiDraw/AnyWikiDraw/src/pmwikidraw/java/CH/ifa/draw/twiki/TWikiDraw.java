/*
 * @(#)TWikiDraw.java 5.1
 * Copyright 2000 by Peter Thoeny, Peter@Thoeny.com.
 * It is hereby granted that this software can be used, copied, 
 * modified, and distributed without fee provided that this 
 * copyright notice appears in all copies.
 * Portions Copyright (C) 2001 Motorola - All Rights Reserved
 */

package CH.ifa.draw.twiki;

import Acme.JPM.Encoders.*;
import CH.ifa.draw.appframe.*;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;
import CH.ifa.draw.figures.*;
import CH.ifa.draw.util.*;
import CH.ifa.draw.applet.*;
import CH.ifa.draw.contrib.*;

import java.applet.Applet;
import java.awt.*;
import java.awt.event.*;
import java.lang.reflect.*;
import java.util.*;
import java.io.*;
import java.net.*;

public  class TWikiDraw extends LightweightDrawApplet {

  public void init()
  {
    String colors = getParameter("extracolors");
    init(new TWikiFrame(this, colors));
    add(new Label("TWikiDraw editing " + getParameter("drawingname")));
  }

    /**
     * x Submits POST command to the server, and reads the reply.
     */
  public boolean post(String url, String fileName, String type, String path,
      String content, String comment) throws MalformedURLException, IOException
  {

    String sep = "89692781418184";
    while (content.indexOf(sep) != -1)
      sep += "x";

    //url= "http://localhost/wiki/pmwiki.php";

    String message = makeMimeForm(fileName, type, path, content, comment, sep);

    // for test
    //URL server = new URL("http", "localhost", 80, savePath);
    /*
     * URL server = new URL( getCodeBase().getProtocol(),
     * getCodeBase().getHost(), getCodeBase().getPort(), url);
     */
    URL server = new URL(url);
    TWikiFrame.debug("Actual URL:" + server.toString());
    URLConnection connection = server.openConnection();

    connection.setAllowUserInteraction(true);
    connection.setDoOutput(true);
    //connection.setDoInput(true);
    connection.setUseCaches(false);

    connection.setRequestProperty("Content-type", "multipart/form-data; boundary=" + sep);
    connection.setRequestProperty("Content-length", Integer.toString(message.length()));

    if (getParameter("debug") != null)
    {
      TWikiFrame.debug(message);
    }
    //System.out.println(url);
    String replyString = null;
    try
    {
      DataOutputStream out = new DataOutputStream(connection.getOutputStream());
      out.writeBytes(message);
      out.close();
      TWikiFrame.debug("Wrote " + message.length() + " bytes to\n" + connection);

      try
      {
        BufferedReader in = new BufferedReader(new InputStreamReader(connection.getInputStream()));
        String reply = null;
        while ((reply = in.readLine()) != null)
        {
          if (reply.startsWith("ERROR "))
          {
            replyString = reply.substring("ERROR ".length());
          }
        }
        in.close();
      } catch (IOException ioe)
      {
        replyString = ioe.toString();
      }
    } catch (UnknownServiceException use)
    {
      replyString = use.getMessage();
      TWikiFrame.debug(message);
    }
    if (replyString != null)
    {
      TWikiFrame.debug("---- Reply " + replyString);
      if (replyString.startsWith("URL "))
      {
        URL eurl = getURL(replyString.substring("URL ".length()));
        getAppletContext().showDocument(eurl);
      } else if (replyString.startsWith("java.io.FileNotFoundException"))
      {
        // debug; when run from appletviewer, the http connection
        // is not available so write the file content
        if (path.endsWith(".draw") || path.endsWith(".map"))
          System.out.println(content);
      } else
        showStatus(replyString);
      return false;
    } else
    {
      showStatus(url + " saved");
      return true;
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
    private String makeMimeForm(String path, String type, String fileName,
      String content, String comment, String sep) {
		
			String binary = "";
			if (type.equals("image/gif")) {
			    binary = "Content-Transfer-Encoding: binary" + NL;
			}
		
			String mime_sep = NL + "--" + sep + NL;
		
			return "--" + sep + "\r\n" 
            + "Content-Disposition: form-data; name=\"upname\"" + NLNL
            + fileName 
            + mime_sep
      			+ "Content-Disposition: form-data; name=\"pagename\"" + NLNL
      			+ path
      			+ mime_sep
            + "Content-Disposition: form-data; name=\"action\"" + NLNL
            + "postupload"
            + mime_sep
            + "Content-Disposition: form-data; name=\"noredirect\"" + NLNL
            + "fish"
            + mime_sep
            + "Content-Disposition: form-data; name=\"uploadfile\"; "
            + "filename=\"" + fileName + "\"" + NL
            + "Content-Type: " + type + NL
            + binary + NL
            + content
            + mime_sep
            + NL + "--" + sep + "--" + NL;
    }

    /** Replace current app with a different URL */
    void exitApplet()
  {
    String viewPath = getParameter(VIEWPATH_PARAMETER);
    if (viewPath != null)
    {
      try
      {
        URL url = new URL(getCodeBase(), viewPath);
        getAppletContext().showDocument(url, "_self");
      } catch (MalformedURLException mue)
      {
        showStatus("Bad URL for viewpath " + viewPath);
      }
    }
  }

    static private String VIEWPATH_PARAMETER   = "viewurl";
}
