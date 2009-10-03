/*
 * @(#)HttpRequest.java
 * 
 * Copyright (c) 2009 by the original authors of AnyWikiDraw
 * and all its contributors.
 * All rights reserved.
 * 
 * The copyright of this software is owned by the authors and  
 * contributors of the AnyWikiDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.anywikidraw.any.io;

import org.anywikidraw.any.io.HtmlForm;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.io.InputStream;
import java.io.UnsupportedEncodingException;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.HashMap;

/**
 * HttpRequest sends a {@code HtmlForm} to a HTTP server using {@code
 * java.net.HttpURLConnection} and reads the response from the server.
 *
 *
 * @author Werner Randelshofer
 * @version $Id$
 */
public class HttpRequest {

    private String requestMethod;
    private URL url;
    private HttpURLConnection connection;

    public static enum States {

        UNSENT, OPENED, SENT, HEADERS_RECEIVED, LOADING, DONE
    };
    private States state = States.UNSENT;
    private int responseCode = -1;
    private String responseMessage;
    private byte[] responseData;

    /**
     * Creates a new HttpRequest.
     */
    public HttpRequest() {
    }

    /**
     * Creates a new HttpRequest and opens it.
     *
     * @param method The request method, usually POST or GET.
     * @param url The url for the request.
     */
    public HttpRequest(String method, URL url) {
        open(method, url);
    }

    /**
     * Opens the request.
     */
    public void open(String method, URL url) {
        if (state != States.UNSENT) {
            throw new IllegalStateException("State must be UNSENT.");
        }

        this.requestMethod = method;
        this.url = url;

        try {
            connection = (HttpURLConnection) url.openConnection();
            connection.setDoOutput(true);
            connection.setDoInput(true);
            state = States.OPENED;
        } catch (IOException ex) {
            state = States.DONE;
            responseCode = -1;
            responseMessage = ex.toString();
            try {
                responseData = responseMessage.getBytes("UTF-8");
            } catch (UnsupportedEncodingException ex1) {
                throw new InternalError("UTF-8 not supported");
            }
        }
    }

    /** Sets a request property. */
    public void setRequestProperty(String key, String value) {
        if (state != States.OPENED) {
            throw new IllegalStateException("State must be UNSENT.");
        }

        connection.setRequestProperty(key, value);
    }

    /** Sends the form to the server. */
    public void send(HtmlForm form) {
        if (state != States.OPENED) {
            throw new IllegalStateException("State must be OPENED");
        }
        String boundary = HtmlForm.createBoundary();
        connection.setRequestProperty("Content-Type",
                "multipart/form-data; boundary=" + boundary);
        try {
            OutputStream out = connection.getOutputStream();
            form.writeForm(out, boundary);
            out.close();
            state = States.SENT;
        } catch (IOException ex) {
            disconnect();
            state = States.DONE;
            responseMessage = ex.toString();
            try {
                responseData = responseMessage.getBytes("UTF-8");
            } catch (UnsupportedEncodingException ex1) {
                throw new InternalError("UTF-8 not supported");
            }
        }
    }

    private void disconnect() {
        if (connection != null) {
            connection.disconnect();
            connection = null;
        }
        state = States.DONE;
    }

    /** Reads the response from the server. */
    private void read() {
        if (state == States.SENT) {
            try {
                responseCode = connection.getResponseCode();
                responseMessage = connection.getResponseMessage();
            } catch (IOException ex) {
                responseMessage = ex.toString();
                try {
                    responseData = responseMessage.getBytes("UTF-8");
                } catch (UnsupportedEncodingException ex1) {
                    throw new InternalError("UTF-8 not supported");
                }
                disconnect();
                return;
            }

            InputStream in = null;
            try {
                in = connection.getInputStream();
            } catch (IOException ex) {
                in = connection.getErrorStream();
            }

            try {
                if (in != null) {
                    byte[] buf = new byte[512];
                    ByteArrayOutputStream tmp = new ByteArrayOutputStream();
                    for (int count = 0; count != -1; count = in.read(buf)) {
                        tmp.write(buf, 0, count);
                    }
                    responseData = tmp.toByteArray();
                }

            } catch (IOException ex) {
                responseMessage = ex.toString();
                try {
                    responseData = responseMessage.getBytes("UTF-8");
                } catch (UnsupportedEncodingException ex1) {
                    throw new InternalError("UTF-8 not supported");
                }
                disconnect();
                return;
            }
        }

        disconnect();
    }

    /** Gets the response code from the server. */
    public int getResponseCode() {
        read();
        return responseCode;
    }

    /** Gets the response message from the server. */
    public String getResponseMessage() {
        read();
        return responseMessage;
    }

    /** Gets the response data from the server as a UTF-8 encoded string. */
    public String getResponseDataAsString() {
        read();
        try {
            return responseData == null ? null : new String(responseData, "UTF-8");
        } catch (UnsupportedEncodingException ex) {
            throw new InternalError("UTF-8 not supported");
        }
    }
}
