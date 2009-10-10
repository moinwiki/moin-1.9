/*
 * @(#)FigureSelection.java 5.1
 *
 */

package CH.ifa.draw.framework;

import CH.ifa.draw.util.*;
import java.util.*;
import java.io.*;

/**
 * FigureSelection enables to transfer the selected figures
 * to a clipboard.<p>
 * Will soon be converted to the JDK 1.1 Transferable interface.
 *
 * @see Clipboard
 */

public class FigureSelection extends Object {

    private byte[] fData; // flattend figures, ready to be resurrected
    /**
     * The type identifier of the selection.
     */
    public final static String TYPE = "CH.ifa.draw.Figures";

    /**
     * Constructes the Figure selection for the vecotor of figures.
     */
    public FigureSelection(Vector figures) {
        // a FigureSelection is represented as a flattened ByteStream
        // of figures.
        ByteArrayOutputStream output = new ByteArrayOutputStream(200);
        StorableOutput writer = new StorableOutput(output);
        writer.writeInt(figures.size());
        Enumeration selected = figures.elements();
        while (selected.hasMoreElements()) {
            Figure figure = (Figure) selected.nextElement();
            writer.writeStorable(figure);
        }
        writer.close();
        fData = output.toByteArray();
    }

    /**
     * Gets the type of the selection.
     */
    public String getType() {
        return TYPE;
    }

    /**
     * Gets the data of the selection. The result is returned
     * as a Vector of Figures.
     *
     * @return a copy of the figure selection.
     */
    public Object getData(String type) {
        if (type.equals(TYPE)) {
            InputStream input = new ByteArrayInputStream(fData);
            Vector result = new Vector(10);
            StorableInput reader = new StorableInput(input);
            int numRead = 0;
            try {
                int count = reader.readInt();
                while (numRead < count) {
                    Figure newFigure = (Figure) reader.readStorable();
                    result.addElement(newFigure);
                    numRead++;
                }
            } catch (IOException e) {
                System.out.println(e.toString());
            }
            return result;
        }
        return null;
    }
}

