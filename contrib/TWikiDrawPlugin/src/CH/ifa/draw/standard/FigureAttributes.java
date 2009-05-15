/*
 * @(#)FigureAttributes.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.util.*;
import java.awt.Color;
import java.io.IOException;
import java.io.Serializable;

import CH.ifa.draw.util.*;
import CH.ifa.draw.framework.*;

/**
 * A container for a figure's attributes. The attributes are stored
 * as key/value pairs.
 *
 * @see Figure
 */

public  class   FigureAttributes
        extends Object
        implements Cloneable, Serializable {

    private Hashtable fMap;

    /*
     * Serialization support.
     */
    private static final long serialVersionUID = -6886355144423666716L;
    private int figureAttributesSerializedDataVersion = 1;

    /**
     * Constructs the FigureAttributes.
     */
    public FigureAttributes() {
        fMap = new Hashtable();
    }

    /**
     * Gets the attribute with the given name.
     * @returns attribute or null if the key is not defined
     */
    public Object get(String name) {
        return fMap.get(name);
    }

    /**
     * Sets the attribute with the given name and
     * overwrites its previous value.
     */
    public void set(String name, Object value) {
        fMap.put(name, value);
    }

    /**
     * Tests if an attribute is defined.
     */
    public boolean hasDefined(String name) {
        return fMap.containsKey(name);
    }

    /**
     * Clones the attributes.
     */
   public Object clone() {
        try {
            FigureAttributes a = (FigureAttributes) super.clone();
            a.fMap = (Hashtable) fMap.clone();
            return a;
        } catch (CloneNotSupportedException e) {
	        throw new InternalError();
        }
    }

    /**
     * Reads the attributes from a StorableInput.
     * FigureAttributes store the following types directly:
     * Color, Boolean, String, Int. Other attribute types
     * have to implement the Storable interface or they
     * have to be wrapped by an object that implements Storable.
     * @see Storable
     * @see #write
     */
    public void read(StorableInput dr) throws IOException {
        String s = dr.readString();
        if (!s.toLowerCase().equals("attributes"))
            throw new IOException("Attributes expected");

        fMap = new Hashtable();
        int size = dr.readInt();
        for (int i=0; i<size; i++) {
            String key = dr.readString();
            String valtype = dr.readString();
            Object val = null;
            if (valtype.equals("Color"))
                val = new Color(dr.readInt(), dr.readInt(), dr.readInt());
            else if (valtype.equals("Boolean"))
                val = new Boolean(dr.readString());
            else if (valtype.equals("String"))
                val = dr.readString();
            else if (valtype.equals("Int"))
                val = new Integer(dr.readInt());
            else if (valtype.equals("Storable"))
                val = dr.readStorable();
            else if (valtype.equals("UNKNOWN"))
                continue;

            fMap.put(key,val);
        }
    }

    /**
     * Writes the attributes to a StorableInput.
     * FigureAttributes store the following types directly:
     * Color, Boolean, String, Int. Other attribute types
     * have to implement the Storable interface or they
     * have to be wrapped by an object that implements Storable.
     * @see Storable
     * @see #write
     */
    public void write(StorableOutput dw) {
        dw.writeString("attributes");

        dw.writeInt(fMap.size());   // number of attributes
        Enumeration k = fMap.keys();
        while (k.hasMoreElements()) {
            String s = (String) k.nextElement();
            dw.writeString(s);
            Object v = fMap.get(s);
            if (v instanceof String) {
                dw.writeString("String");
                dw.writeString((String) v);
            } else if (v instanceof Color) {
                dw.writeString("Color");
                dw.writeInt(((Color)v).getRed());
                dw.writeInt(((Color)v).getGreen());
                dw.writeInt(((Color)v).getBlue());
            } else if (v instanceof Boolean) {
                dw.writeString("Boolean");
                if (((Boolean)v).booleanValue())
                    dw.writeString("TRUE");
                else
                    dw.writeString("FALSE");
            } else if (v instanceof Integer) {
                dw.writeString("Int");
                dw.writeInt(((Integer)v).intValue());
            } else if (v instanceof Storable) {
                dw.writeString("Storable");
                dw.writeStorable((Storable)v);
            } else {
                System.out.println(v);
                dw.writeString("UNKNOWN");
            }
        }
    }
}

