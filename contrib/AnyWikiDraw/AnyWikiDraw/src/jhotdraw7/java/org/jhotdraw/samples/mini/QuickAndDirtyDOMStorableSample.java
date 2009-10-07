/*
 * @(#)QuickAndDirtyDOMStorableSample.java
 * 
 * Copyright (c) 2009 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 * 
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.samples.mini;

import org.jhotdraw.xml.*;
import java.io.IOException;
import java.io.StringReader;
import java.io.StringWriter;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * {@code QuickAndDirtyDOMStorableSample} serializes a DOMStorable MyObject into
 * a String using the QuickAnddirtyDOMFactory and then deserializes it from the
 * String.
 *
 * @author Werner Randelshofer
 * @version $Id: QuickAndDirtyDOMStorableSample.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class QuickAndDirtyDOMStorableSample {

    public static class MyObject implements DOMStorable {

        private String name;

        /** DOM Storable objects must have a non-argument constructor. */
        public MyObject() {
        }

        public MyObject(String name) {
            this.name = name;
        }

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public void write(DOMOutput out) throws IOException {
            out.addAttribute("name", name);
        }

        public void read(DOMInput in) throws IOException {
            name = in.getAttribute("name", null);
        }
    }

    public static void main(String[] args) {
        try {
            // Create a DOMStorable object
            MyObject obj = new MyObject("Hello World");
            System.out.println("The name of the original object is:" + obj.getName());

            // Write the object into a DOM, and then serialize the DOM into a String
            NanoXMLDOMOutput out = new NanoXMLDOMOutput(new QuickAndDirtyDOMFactory());
            out.writeObject(obj);

            StringWriter writer = new StringWriter();
            out.save(writer);
            String serializedString = writer.toString();

            System.out.println("\nThe serialized representation of the object is:\n" + serializedString);

            // Deserialize a DOM from a String, and then read the object from the DOM
            StringReader reader = new StringReader(serializedString);
            NanoXMLDOMInput in = new NanoXMLDOMInput(new QuickAndDirtyDOMFactory(), reader);
            MyObject obj2 = (MyObject) in.readObject();

            System.out.println("\nThe name of the restored object is:" + obj2.getName());
        } catch (IOException ex) {
            Logger.getLogger(QuickAndDirtyDOMStorableSample.class.getName()).log(Level.SEVERE, null, ex);
        }

    }
}
