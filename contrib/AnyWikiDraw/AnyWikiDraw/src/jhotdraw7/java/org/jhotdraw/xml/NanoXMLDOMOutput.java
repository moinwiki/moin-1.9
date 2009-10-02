/*
 * @(#)NanoXMLDOMOutput.java
 *
 * Copyright (c) 1996-2009 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.xml;

import java.awt.*;
import java.util.*;
import java.io.*;
import net.n3.nanoxml.*;
import org.jhotdraw.beans.Disposable;
/**
 * DOMOutput using Nano XML.
 * <p>
 * Design pattern:<br>
 * Name: Adapter.<br>
 * Role: Adapter.<br>
 * Partners: {@link net.n3.nanoxml.XMLElement} as Adaptee.
 *
 * @author  Werner Randelshofer
 * @version $Id: NanoXMLDOMOutput.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class NanoXMLDOMOutput implements DOMOutput, Disposable {
    
    
    /**
     * The doctype of the XML document.
     */
    private String doctype;
    /**
     * This map is used to marshall references to objects to
     * the XML DOM. A key in this map is a Java Object, a value in this map
     * is String representing a marshalled reference to that object.
     */
    private HashMap<Object,String> objectids;
    /**
     * This map is used to cache prototype objects.
     */
    private HashMap<String,Object> prototypes;
    
    /**
     * The document used for output.
     */
    private XMLElement document;
    /**
     * The current node used for output.
     */
    private XMLElement current;
    /**
     * The factory used to create objects.
     */
    private DOMFactory factory;
    /**
     * The stack.
     */
    private Stack<XMLElement> stack;
    
    /** Creates a new instance. */
    public NanoXMLDOMOutput(DOMFactory factory) {
        this.factory = factory;
        objectids = new HashMap<Object,String>();
        document = new XMLElement();//new HashMap(), false, false);
        current = document;
        stack = new Stack<XMLElement>();
        stack.push(current);
    }
    
    /**
     * Writes the contents of the DOMOutput into the specified output stream.
     */
    public void save(OutputStream out) throws IOException {
        Writer w = new OutputStreamWriter(out, "UTF8");
        save(w);
        w.flush();
    }
    /**
     * Writes the contents of the DOMOutput into the specified writer.
     */
    public void save(Writer out) throws IOException {
        if (doctype != null) {
            out.write("<!DOCTYPE ");
            out.write(doctype);
            out.write(">\n");
        }
        XMLWriter writer = new XMLWriter(out);
        writer.write((XMLElement) document.getChildren().get(0));
    }
    /**
     * Prints the contents of the DOMOutput into the specified print writer.
     */
    public void print(PrintWriter out) {
        XMLWriter writer = new XMLWriter(out);
        
        try {
            // writer.write(document);
            writer.write((XMLElement) document.getChildren().get(0), true);
        } catch (IOException e) {
            InternalError error = new InternalError();
            error.initCause(e);
            throw error;
        }
        //((XMLElement) document.getChildren().get(0)).print(out);
    }
    
    /**
     * Puts a new element into the DOM Document.
     * The new element is added as a child to the current element in the DOM
     * document. Then it becomes the current element.
     * The element must be closed using closeElement.
     */
    public void openElement(String tagName) {
        XMLElement newElement = new XMLElement();//new HashMap(), false, false);
        newElement.setName(tagName);
        current.addChild(newElement);
        stack.push(current);
        current = newElement;
    }
    /**
     * Closes the current element of the DOM Document.
     * The parent of the current element becomes the current element.
     * @exception IllegalArgumentException if the provided tagName does
     * not match the tag name of the element.
     */
    public void closeElement() {
        current = (XMLElement) stack.pop();
    }
    /**
     * Adds a comment to the current element of the DOM Document.
     */
    public void addComment(String comment) {
        // NanoXML does not support comments
    }
    /**
     * Adds a text to current element of the DOM Document.
     * Note: Multiple consecutives texts will be merged.
     */
    public void addText(String text) {
        String old = current.getContent();
        if (old == null) {
            current.setContent(text);
        } else {
            current.setContent(old+text);
        }
    }
    /**
     * Adds an attribute to current element of the DOM Document.
     */
    public void addAttribute(String name, String value) {
        if (value != null) {
            current.setAttribute(name, value);
        }
    }
    /**
     * Adds an attribute to current element of the DOM Document.
     */
    public void addAttribute(String name, int value) {
        current.setAttribute(name, Integer.toString(value));
    }
    /**
     * Adds an attribute to current element of the DOM Document.
     */
    public void addAttribute(String name, boolean value) {
        current.setAttribute(name, new Boolean(value).toString());
    }
    /**
     * Adds an attribute to current element of the DOM Document.
     */
    public void addAttribute(String name, float value) {
        // Remove the awkard .0 at the end of each number
        String str = Float.toString(value);
        if (str.endsWith(".0")) str = str.substring(0, str.length() - 2);
        current.setAttribute(name, str);
    }
    /**
     * Adds an attribute to current element of the DOM Document.
     */
    public void addAttribute(String name, double value) {
        // Remove the awkard .0 at the end of each number
        String str = Double.toString(value);
        if (str.endsWith(".0")) str = str.substring(0, str.length() - 2);
        current.setAttribute(name, str);
    }
    
    public void writeObject(Object o) throws IOException {
        if (o == null) {
            openElement("null");
            closeElement();
        } else if (o instanceof DOMStorable) {
            writeStorable((DOMStorable) o);
        } else if (o instanceof String) {
            openElement("string");
            addText((String) o);
            closeElement();
        } else if (o instanceof Integer) {
            openElement("int");
            addText(o.toString());
            closeElement();
        } else if (o instanceof Long) {
            openElement("long");
            addText(o.toString());
            closeElement();
        } else if (o instanceof Double) {
            openElement("double");
            // Remove the awkard .0 at the end of each number
            String str = o.toString();
            if (str.endsWith(".0")) str = str.substring(0, str.length() - 2);
            addText(str);
            closeElement();
        } else if (o instanceof Float) {
            openElement("float");
            // Remove the awkard .0 at the end of each number
            String str = o.toString();
            if (str.endsWith(".0")) str = str.substring(0, str.length() - 2);
            addText(str);
            closeElement();
        } else if (o instanceof Boolean) {
            openElement("boolean");
            addText(o.toString());
            closeElement();
        } else if (o instanceof Color) {
            Color c = (Color) o;
            openElement("color");
            addAttribute("rgba", "#"+Integer.toHexString(c.getRGB()));
            closeElement();
        } else if (o instanceof int[]) {
            openElement("intArray");
            int[] a = (int[]) o;
            for (int i=0; i < a.length; i++) {
                writeObject(new Integer(a[i]));
            }
            closeElement();
        } else if (o instanceof float[]) {
            openElement("floatArray");
            float[] a = (float[]) o;
            for (int i=0; i < a.length; i++) {
                writeObject(new Float(a[i]));
            }
            closeElement();
        } else if (o instanceof double[]) {
            openElement("doubleArray");
            double[] a = (double[]) o;
            for (int i=0; i < a.length; i++) {
                writeObject(new Double(a[i]));
            }
            closeElement();
        } else if (o instanceof Font) {
            Font f = (Font) o;
            openElement("font");
            addAttribute("name", f.getName());
            addAttribute("style", f.getStyle());
            addAttribute("size", f.getSize());
            closeElement();
        } else if (o instanceof Enum) {
            openElement("enum");
            Enum e = (Enum) o;
            addAttribute("type", factory.getEnumName(e));
            addText(factory.getEnumValue(e));
            closeElement();
        } else {
            throw new IllegalArgumentException("unable to store: "+o+" "+o.getClass());
        }
    }
    private XMLElement writeStorable(DOMStorable o) throws IOException {
        String tagName = factory.getName(o);
        if (tagName == null) throw new IllegalArgumentException("no tag name for:"+o);
        openElement(tagName);
        XMLElement element = current;
        if (objectids.containsKey(o)) {
            addAttribute("ref", (String) objectids.get(o));
        } else {
            String id = Integer.toString(objectids.size(), 16);
            objectids.put(o, id);
            addAttribute("id", id);
            o.write(this);
        }
        closeElement();
        return element;
    }
    
    public void addAttribute(String name, float value, float defaultValue) {
        if (value != defaultValue) {
            addAttribute(name, value);
        }
    }
    
    public void addAttribute(String name, int value, int defaultValue) {
        if (value != defaultValue) {
            addAttribute(name, value);
        }
    }
    
    public void addAttribute(String name, double value, double defaultValue) {
        if (value != defaultValue) {
            addAttribute(name, value);
        }
    }
    
    public void addAttribute(String name, boolean value, boolean defaultValue) {
        if (value != defaultValue) {
            addAttribute(name, value);
        }
    }
    
    public void addAttribute(String name, String value, String defaultValue) {
        if (value != null && ! value.equals(defaultValue)) {
            addAttribute(name, value);
        }
    }
    
    public Object getPrototype() {
        if (prototypes == null) {
            prototypes = new HashMap<String, Object>();
        }
        if (! prototypes.containsKey(current.getName())) {
            prototypes.put(current.getName(), factory.create(current.getName()));
        }
        return prototypes.get(current.getName());
    }
    
    public void setDoctype(String doctype) {
        this.doctype = doctype;
    }

    public void dispose() {
        if (document != null) {
            document.dispose();
            document = null;
        }
    }
}