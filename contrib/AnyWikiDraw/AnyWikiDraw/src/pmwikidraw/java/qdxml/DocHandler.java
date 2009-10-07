package qdxml;

import java.util.*;

public interface DocHandler {
  public void startElement(String tag,Hashtable h) throws Exception;
  public void endElement(String tag) throws Exception;
  public void startDocument() throws Exception;
  public void endDocument() throws Exception;
  public void text(String str) throws Exception;
}
