/*
 * @(#)HtmlForm.java
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

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;

/**
 * Holds the data fields of a HTML form.
 *
 * @author Werner Randelshofer
 * @version $Id$
 */
public class HtmlForm {

    private static Random random = new Random();

    protected static String randomString() {
        return Long.toString(random.nextLong(), 36);
    }
    public static String createBoundary() {
    return "---------------------------" + randomString() + randomString() + randomString();
    }


    public abstract static class Parameter {

        String name;

        protected abstract void writeParameter(OutputStream out, String boundary) throws IOException;

        protected void write(OutputStream out, String s) throws IOException {
            out.write(s.getBytes("UTF-8"));
        }

        protected void newline(OutputStream out) throws IOException {
            out.write("\r\n".getBytes("UTF-8"));
        }

        protected void writeln(OutputStream out, String s) throws IOException {
            write(out, s);
            newline(out);
        }

        protected void writeName(OutputStream out, String name) throws IOException {
            newline(out);
            write(out, "Content-Disposition: form-data; name=\"");
            write(out, name);
            write(out, "\"");
        }
    }

    public static class StringParameter extends Parameter {

        String value;

        protected void writeParameter(OutputStream out, String boundary) throws IOException {
            write(out, "--");
            write(out, boundary);
            writeName(out, name);
            newline(out);
            newline(out);
            writeln(out, value);
        }
    }

    public static class FileParameter extends Parameter {

        String filename;
        String contentType;
        byte[] data;

        protected void writeParameter(OutputStream out, String boundary) throws IOException {
            write(out, "--");
            write(out, boundary);
            writeName(out, name);
            write(out, "; filename=\"");
            write(out, filename);
            write(out, "\"");
            newline(out);
            write(out, "Content-Type: ");
            String type = contentType;//URLConnection.guessContentTypeFromName(filename);
            if (type == null) {
                type = "application/octet-stream";
            }
            writeln(out, type);
            newline(out);
            out.write(data);
            newline(out);
        }
    }
    private HashMap<String, Parameter> parameters = new HashMap<String, Parameter>();

    /** Adds a string parameter to the form.
     *
     * @param name the parameter name
     * @param value the parameter value
     */
    public void putString(String name, String value) {
        StringParameter entry = new StringParameter();
        entry.name = name;
        entry.value = value;
        parameters.put(name, entry);
    }

    /** Adds a file parameter to the form.
     *
     * @param name the parameter name
     * @param filename the file name
     * @param contentType the Mime Type of the file
     * @param data the contents of the file
     */
    public void putFile(String name, String filename, String contentType, byte[] data) {
        FileParameter entry = new FileParameter();
        entry.name = name;
        entry.filename = filename;
        entry.contentType = contentType;
        entry.data = data;
        parameters.put(name, entry);
    }

    /** Adds a file parameter to the form.
     *
     * @param name the parameter name
     * @param filename the file name
     * @param contentType the Mime Type of the file
     * @param in the contents of the file
     */
    public void putFile(String name, String filename, String contentType, InputStream in) throws IOException {
        FileParameter entry = new FileParameter();
        entry.name = name;
        entry.filename = filename;
        entry.contentType = contentType;

        byte[] buf = new byte[512];
        ByteArrayOutputStream tmp = new ByteArrayOutputStream();
        for (int len = 0; len != -1; len = in.read(buf)) {
            tmp.write(buf, 0, len);
        }

        entry.data = tmp.toByteArray();
        parameters.put(name, entry);
    }

    public Map<String, Parameter> getParameters() {
        return parameters;
    }

    /** Writes the form to the specified output stream. */
    public void writeForm(OutputStream out) throws IOException {
        writeForm(out, createBoundary());
    }

    /** Writes the form to the specified output stream. */
    public void writeForm(OutputStream out, String boundary) throws IOException {
        for (Parameter p : parameters.values()) {
            p.writeParameter(out, boundary);
        }
        out.write(("--" + boundary + "\r\n--").getBytes("UTF-8"));
    }
}
