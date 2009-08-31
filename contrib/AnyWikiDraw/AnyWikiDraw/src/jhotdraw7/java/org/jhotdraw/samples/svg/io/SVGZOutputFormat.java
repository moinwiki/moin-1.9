/*
 * @(#)SVGZOutputFormat.java
 *
 * Copyright (c) 1996-2007 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.samples.svg.io;

import java.io.*;
import java.util.zip.*;
import javax.swing.*;
import org.jhotdraw.draw.*;
import org.jhotdraw.io.*;

/**
 * SVGZOutputFormat.
 *
 * @author Werner Randelshofer
 * @version $Id: SVGZOutputFormat.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class SVGZOutputFormat extends SVGOutputFormat {
    
    /** Creates a new instance. */
    public SVGZOutputFormat() {
    }
    
    public String getFileExtension() {
        return "svgz";
    }
    public javax.swing.filechooser.FileFilter getFileFilter() {
        return new ExtensionFileFilter("Compressed Scalable Vector Graphics (SVGZ)", "svgz");
    }
    
    
    @Override public void write(OutputStream out, Drawing drawing) throws IOException {
        GZIPOutputStream gout = new GZIPOutputStream(out);
        super.write(gout, drawing, drawing.getChildren());
        gout.finish();
        
    }
}
