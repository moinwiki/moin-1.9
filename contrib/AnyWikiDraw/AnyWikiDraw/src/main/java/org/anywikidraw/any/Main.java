/*
 * @(#)Main.java
 *
 * Copyright (c) 1996-2006 by the original authors of AnyWikiDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the AnyWikiDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.anywikidraw.any;

import org.jhotdraw.app.*;
import org.jhotdraw.samples.svg.SVGApplicationModel;
import org.jhotdraw.util.ResourceBundleUtil;
/**
 * Main.
 *
 * @author Werner Randelshofer.
 * @version $Id: Main.java 107 2009-06-15 19:33:05Z rawcoder $
 */
public class Main {
    
    /** Creates a new instance. */
    public static void main(String[] args) {
        ResourceBundleUtil.setVerbose(true);

        Application app;
        String os = System.getProperty("os.name").toLowerCase();
        if (os.startsWith("mac")) {
            app = new DefaultOSXApplication();
        } else if (os.startsWith("win")) {
          //  app = new DefaultMDIApplication();
            app = new DefaultSDIApplication();
        } else {
            app = new DefaultSDIApplication();
        }
        
        //WikiDrawApplicationModel model = new WikiDrawApplicationModel();
        SVGApplicationModel model = new SVGApplicationModel();
        model.setName("AnyWikiDraw SVG");
        model.setVersion("0.11");
        model.setCopyright("Copyright 2007 (c) by the authors of the AnyWikiDraw project\n" +
                "This software is licensed under LGPL or Creative Commons 2.5 BY");
        //model.setProjectClassName("org.anywikidraw.any.WikiDrawProject");
        model.setViewClassName("org.jhotdraw.samples.svg.SVGView");
        app.setModel(model);
        app.launch(args);
    }
    
}
