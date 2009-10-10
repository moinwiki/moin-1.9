/*
 * @(#)DOMOutput.java
 *
 * Copyright (c) 1996-2006 by the original authors of JHotDraw
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
import javax.xml.parsers.*;
import javax.xml.transform.*;
import javax.xml.transform.dom.*;
import javax.xml.transform.stream.*;
import org.w3c.dom.*;
import java.io.*;
/**
 * DOMOutput.
 * <p>
 * Design pattern:<br>
 * Name: Adapter.<br>
 * Role: Adapter.<br>
 * Partners: {@link org.w3c.dom.Document} as Adaptee.
 *
 * @author  Werner Randelshofer
 * @version $Id: JavaxDOMOutput.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class JavaxDOMOutput implements DOMOutput {
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
    private Document document;
    /**
     * The current node used for output.
     */
    private Node current;
    /**
     * The factory used to create objects.
     */
    private DOMFactory factory;
    
    /** Creates a new instance. */
    public JavaxDOMOutput(DOMFactory factory) throws IOException {
        this.factory = factory;
        }
    protected void reset() throws IOException {
        try {
            objectids = new HashMap<Object,String>();
            document = DocumentBuilderFactory.newInstance().newDocumentBuilder().newDocument();
            current = document;
        } catch (ParserConfigurationException e) {
            IOException error = new IOException(e.getMessage());
            error.initCause(e);
            throw error;
        }
    }
    
    /**
     * Writes the contents of the DOMOutput into the specified output stream.
     */
    public void save(OutputStream out) throws IOException {
        reset();
        try {
            if (doctype != null) {
                OutputStreamWriter w = new OutputStreamWriter(out, "UTF8");
                w.write("<!DOCTYPE ");
                w.write(doctype);
                w.write(">\n");
                w.flush();
            }
            Transformer t = TransformerFactory.newInstance().newTransformer();
            t.transform(new DOMSource(document), new StreamResult(out));
        } catch (TransformerException e) {
            IOException error = new IOException(e.getMessage());
            error.initCause(e);
            throw error;
        }
    }
    /**
     * Writes the contents of the DOMOutput into the specified output stream.
     */
    public void save(Writer out) throws IOException {
        reset();
        try {
            if (doctype != null) {
                out.write("<!DOCTYPE ");
                out.write(doctype);
                out.write(">\n");
            }
            Transformer t = TransformerFactory.newInstance().newTransformer();
            t.transform(new DOMSource(document), new StreamResult(out));
        } catch (TransformerException e) {
            IOException error = new IOException(e.getMessage());
            error.initCause(e);
            throw error;
        }
    }
    
    /**
     * Puts a new element into the DOM Document.
     * The new element is added as a child to the current element in the DOM
     * document. Then it becomes the current element.
     * The element must be closed using closeElement.
     */
    public void openElement(String tagName) {
        Element newElement = document.createElement(tagName);
        current.appendChild(newElement);
        current = newElement;
    }
    /**
     * Closes the current element of the DOM Document.
     * The parent of the current element becomes the current element.
     * @exception IllegalArgumentException if the provided tagName does
     * not match the tag name of the element.
     */
    public void closeElement() {
        /*
        if (! ((Element) current).getName().equals(tagName)) {
            throw new IllegalArgumentException("Attempt to close wrong element:"+tagName +"!="+((Element) current).getName());
        }*/
        current = current.getParentNode();
    }
    /**
     * Adds a comment to the current element of the DOM Document.
     */
    public void addComment(String comment) {
        current.appendChild(document.createComment(comment));
    }
    /**
     * Adds a text to current element of the DOM Document.
     * Note: Multiple consecutives texts will be merged.
     */
    public void addText(String text) {
        current.appendChild(document.createTextNode(text));
    }
    /**
     * Adds an attribute to current element of the DOM Document.
     */
    public void addAttribute(String name, String value) {
        if (value != null) {
            ((Element) current).setAttribute(name, value);
        }
    }
    /**
     * Adds an attribute to current element of the DOM Document.
     */
    public void addAttribute(String name, int value) {
        ((Element) current).setAttribute(name, Integer.toString(value));
    }
    /**
     * Adds an attribute to current element of the DOM Document.
     */
    public void addAttribute(String name, boolean value) {
        ((Element) current).setAttribute(name, Boolean.toString(value));
    }
    /**
     * Adds an attribute to current element of the DOM Document.
     */
    public void addAttribute(String name, float value) {
        // Remove the awkard .0 at the end of each number
        String str = Float.toString(value);
        if (str.endsWith(".0")) str = str.substring(0, str.length() - 2);
        ((Element) current).setAttribute(name, str);
    }
    /**
     * Adds an attribute to current element of the DOM Document.
     */
    public void addAttribute(String name, double value) {
        // Remove the awkard .0 at the end of each number
        String str = Double.toString(value);
        if (str.endsWith(".0")) str = str.substring(0, str.length() - 2);
        ((Element) current).setAttribute(name, str);
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
            addText(o.toString());
            closeElement();
        } else if (o instanceof Float) {
            openElement("float");
            addText(o.toString());
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
    private void writeStorable(DOMStorable o) throws IOException {
        String tagName = factory.getName(o);
        if (tagName == null) throw new IllegalArgumentException("no tag name for:"+o);
        openElement(tagName);
        if (objectids.containsKey(o)) {
            addAttribute("ref", (String) objectids.get(o));
        } else {
            String id = Integer.toString(objectids.size(), 16);
            objectids.put(o, id);
            addAttribute("id", id);
            o.write(this);
        }
        closeElement();
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
        if (! value.equals(defaultValue)) {
            addAttribute(name, value);
        }
    }

    public Object getPrototype() {
        if (prototypes == null) {
            prototypes = new HashMap<String, Object>();
        }
        if (! prototypes.containsKey(current.getNodeName())) {
            prototypes.put(current.getNodeName(), factory.create(current.getNodeName()));
        }
        return prototypes.get(current.getNodeName());
    }

    public void setDoctype(String doctype) {
        this.doctype = doctype;
    }
}
