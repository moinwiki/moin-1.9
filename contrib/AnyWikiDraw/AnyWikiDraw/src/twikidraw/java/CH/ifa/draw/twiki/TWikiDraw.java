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
    
    public void	init() {
        String colors = getParameter("extracolors");
        init(new TWikiFrame(this, colors));
        String drawPath = getParameter("drawpath");
        add(new Label("TWikiDraw editing " + drawPath));
    }
    
    /**
     * Submits POST command to the server, and reads the reply.
     */
    public boolean post(
                        String url,
                        String fileName,
                        String type,
                        String path,
                        String content,
                        String comment)
        throws IOException {
        
        String sep = "89692781418184";
        while (content.indexOf(sep) != -1)
            sep += "x";
        
        String message = makeMimeForm(fileName, type,
                                      path, content, comment, sep);
        
        // for test
        //URL server = new URL("http", "localhost", 80, savePath);
        URL server = new URL(
                             getCodeBase().getProtocol(),
                             getCodeBase().getHost(),
                             getCodeBase().getPort(),
                             url);
        URLConnection connection = server.openConnection();
        
        connection.setAllowUserInteraction(false);
        connection.setDoOutput(true);
        //connection.setDoInput(true);
        connection.setUseCaches(false);
        
        connection.setRequestProperty(
                                      "Content-type",
                                      "multipart/form-data; boundary=" + sep);
        connection.setRequestProperty(
                                      "Content-length",
                                      Integer.toString(message.length()));
        
        //System.out.println(url);
        String replyString = null;
        try {
            DataOutputStream out =
                new DataOutputStream(connection.getOutputStream());
            out.writeBytes(message);
            out.close();
            //System.out.println("Wrote " + message.length() +
            //		   " bytes to\n" + connection);
            
            try {
                BufferedReader in =
                    new BufferedReader(new InputStreamReader(
                                                             connection.getInputStream()));
                String reply = null;
                while ((reply = in.readLine()) != null) {
                    if (reply.startsWith("ERROR ")) {
                        replyString = reply.substring("ERROR ".length());
                    }
                }
                in.close();
            } catch (IOException ioe) {
                replyString = ioe.toString();
            }
        } catch (UnknownServiceException use) {
            replyString = use.getMessage();
            System.out.println(message);
        }
        if (replyString != null) {
            //System.out.println("---- Reply " + replyString);
            if (replyString.startsWith("URL ")) {
                URL eurl = getURL(replyString.substring("URL ".length()));
                getAppletContext().showDocument(eurl);
            } else if (replyString.startsWith("java.io.FileNotFoundException")) {
                // debug; when run from appletviewer, the http connection
                // is not available so write the file content
                if (path.endsWith(".draw") || path.endsWith(".map"))
                    System.out.println(content);
            } else
                showStatus(replyString);
            return false;
        } else {
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
    private String makeMimeForm(
                                String fileName,
                                String type,
                                String path,
                                String content,
                                String comment,
                                String sep) {
        
        String binary = "";
        if (type.equals("image/gif")) {
            binary = "Content-Transfer-Encoding: binary" + NL;
        }
        
        String mime_sep = NL + "--" + sep + NL;
        
        return
            "--" + sep + "\r\n" 
            + "Content-Disposition: form-data; name=\"filename\"" + NLNL
            + fileName
            + mime_sep
            + "Content-Disposition: form-data; name=\"noredirect\"" + NLNL
            + 1
            + mime_sep
            + "Content-Disposition: form-data; name=\"filepath\"; "
            + "filename=\"" + path + "\"" + NL
            + "Content-Type: " + type + NL
            + binary + NL
            + content
            + mime_sep
            + "Content-Disposition: form-data; name=\"filecomment\"" + NLNL
            + comment
            + NL + "--" + sep + "--" + NL;
    }
    
    /** Replace current app with a different URL */
    public void exit() {
        String viewPath = getParameter(VIEWPATH_PARAMETER);
        if (viewPath != null) {
            try {
                URL url = getURL(viewPath);
                getAppletContext().showDocument(url, "_self");
            } catch (IOException mue) {
                showStatus("Bad URL for viewpath " + viewPath);
            }
        }
    }
    
    static private String VIEWPATH_PARAMETER   = "viewpath";
}
