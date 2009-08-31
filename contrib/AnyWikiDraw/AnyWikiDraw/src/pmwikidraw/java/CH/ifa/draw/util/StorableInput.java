/*
 * @(#)StorableInput.java 5.1
 *
 */

package CH.ifa.draw.util;

import java.util.*;
import java.io.*;
import java.awt.Color;

/**
 * An input stream that can be used to resurrect Storable objects.
 * StorableInput preserves the object identity of the stored objects.
 *
 * @see Storable
 * @see StorableOutput
 */

public  class StorableInput
        extends Object {

    private StreamTokenizer fTokenizer;
    private Vector          fMap;

    /**
     * Initializes a Storable input with the given input stream.
     */
    public StorableInput(InputStream stream) {
        Reader r = new BufferedReader(new InputStreamReader(stream));
        fTokenizer = new StreamTokenizer(r);
        fMap = new Vector();
    }

    /**
     * Reads and resurrects a Storable object from the input stream.
     */
    public Storable readStorable() throws IOException {
        Storable storable;
        String s = readString();

        if (s.equals("NULL"))
            return null;

        if (s.equals("REF")) {
            int ref = readInt();
            return (Storable) retrieve(ref);
        }

        storable = (Storable) makeInstance(s);
        map(storable);
        storable.read(this);
        return storable;
    }

    /**
     * Determine if the next input token is a valid number or not
     */
    public boolean testForNumber() throws IOException {
        int token = fTokenizer.nextToken();
	fTokenizer.pushBack();
        return (token == StreamTokenizer.TT_NUMBER);
    }

    /**
     * Reads a string from the input stream.
     */
    public String readString() throws IOException {
        int token = fTokenizer.nextToken();
        if (token == StreamTokenizer.TT_WORD || token == '"') {
            return fTokenizer.sval;
        }

        String msg = "String expected in line: " + fTokenizer.lineno();
        throw new IOException(msg);
    }

    /**
     * Reads an int from the input stream.
     */
    public int readInt() throws IOException {
        int token = fTokenizer.nextToken();
        if (token == StreamTokenizer.TT_NUMBER)
            return (int) fTokenizer.nval;

        String msg = "Integer expected in line: " + fTokenizer.lineno();
        throw new IOException(msg);
    }

    /**
     * Reads a color from the input stream.
     */
    public Color readColor() throws IOException {
        return new Color(readInt(), readInt(), readInt());
    }

    /**
     * Reads a double from the input stream.
     */
    public double readDouble() throws IOException {
        int token = fTokenizer.nextToken();
        if (token == StreamTokenizer.TT_NUMBER)
            return fTokenizer.nval;

        String msg = "Double expected in line: " + fTokenizer.lineno();
        throw new IOException(msg);
    }

    /**
     * Reads a boolean from the input stream.
     */
    public boolean readBoolean() throws IOException {
        int token = fTokenizer.nextToken();
        if (token == StreamTokenizer.TT_NUMBER)
            return ((int) fTokenizer.nval) == 1;

        String msg = "Integer expected in line: " + fTokenizer.lineno();
        throw new IOException(msg);
    }

    private Object makeInstance(String className) throws IOException {
        try {
            Class cl = Class.forName(className);
            return cl.newInstance();
        } catch (NoSuchMethodError e) {
            throw new IOException("Class " + className
                + " does not seem to have a no-arg constructor");
        } catch (ClassNotFoundException e) {
            throw new IOException("No class: " + className);
        } catch (InstantiationException e) {
            throw new IOException("Cannot instantiate: " + className);
        } catch (IllegalAccessException e) {
            throw new IOException("Class (" + className + ") not accessible");
        }
    }

    private void map(Storable storable) {
        if (!fMap.contains(storable))
            fMap.addElement(storable);
    }

    private Storable retrieve(int ref) {
        return (Storable) fMap.elementAt(ref);
    }
}
