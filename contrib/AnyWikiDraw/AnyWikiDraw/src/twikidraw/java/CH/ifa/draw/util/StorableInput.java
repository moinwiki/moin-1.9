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
            return unescapeUnicode(fTokenizer.sval);
        }

        String msg = "String expected in line: " + fTokenizer.lineno();
        throw new IOException(msg);
    }

    /**
     * from StringEscapeUtils.java in the jakarta-commons
     * Won-kyu Park 22-11-2004
     *
     * <p>Unescapes any Java literals found in the <code>String</code> to a
     * <code>Writer</code>.</p>
     *
     * <p>For example, it will turn a sequence of <code>'\'</code> and
     * <code>'n'</code> into a newline character, unless the <code>'\'</code>
     * is preceded by another <code>'\'</code>.</p>
     *
     * <p>A <code>null</code> string input has no effect.</p>
     *
     * @param out  the <code>Writer</code> used to output unescaped characters
     * @param str  the <code>String</code> to unescape, may be null
     * @throws IllegalArgumentException if the Writer is <code>null</code>
     * @throws IOException if error occurs on underlying Writer
     */
    public static String unescapeUnicode(String str) throws IOException {
        StringBuffer sbuf = new StringBuffer();
        if (str == null) {
            return null;
        }
        int sz = str.length();
        StringBuffer unicode = new StringBuffer(4);
        boolean hadSlash = false;
        boolean inUnicode = false;
        for (int i = 0; i < sz; i++) {
            char ch = str.charAt(i);
            if (inUnicode) {
                // if in unicode, then we're reading unicode
                // values in somehow
                unicode.append(ch);
                if (unicode.length() == 4) {
                    // unicode now contains the four hex digits
                    // which represents our unicode character
                    try {
                        int value = Integer.parseInt(unicode.toString(), 16);
                        sbuf.append((char) value);
                        unicode.setLength(0);
                        inUnicode = false;
                        hadSlash = false;
                    } catch (NumberFormatException nfe) {
                        // simply ignore it.
                        sbuf.append(unicode);
                    }
                }
                continue;
            }
            if (hadSlash) {
                // handle an escaped value
                hadSlash = false;
                switch (ch) {
                    case '\\':
                        sbuf.append('\\');
                        break;
                    case '\'':
                        sbuf.append('\'');
                        break;
                    case '\"':
                        sbuf.append('"');
                        break;
                    case 'r':
                        sbuf.append('\r');
                        break;
                    case 'f':
                        sbuf.append('\f');
                        break;
                    case 't':
                        sbuf.append('\t');
                        break;
                    case 'n':
                        sbuf.append('\n');
                        break;
                    case 'b':
                        sbuf.append('\b');
                        break;
                    case 'u':
                        {
                            // uh-oh, we're in unicode country....
                            inUnicode = true;
                            break;
                        }
                    default :
                        sbuf.append(ch);
                        break;
                }
                continue;
            } else if (ch == '\\') {
                hadSlash = true;
                continue;
            }
            sbuf.append(ch);
        }
        if (hadSlash) {
            // then we're in the weird case of a \ at the end of the
            // string, let's output it anyway.
            sbuf.append('\\');
        }
        return sbuf.toString();
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
