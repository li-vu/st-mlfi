# omlfi type commands
from __future__ import print_function
import sublime
import sublime_plugin
import subprocess
from traceback import print_exc
import sys,os, time
import tempfile
import re
try:
    from .intervaltree import intervaltree
    from .annotparser import AnnotParser
    from .point import Point
except SystemError:
    from intervaltree import intervaltree
    from annotparser import AnnotParser
    from point import Point

try:
    annot_parser
    mlfitype_view_name
    mlfitype_panel_name
except NameError:
    annot_parser = AnnotParser(lex_optimize=True, yacc_debug=False, yacc_optimize=True)
    mlfitype_view_name = "** mlfi types **"
    mlfitype_panel_name = 'mlfi_type_st3_output'

class MlfiTypeCommand(sublime_plugin.TextCommand):
    def __init__(self, *args, **kwargs):
      super(MlfiTypeCommand, self).__init__(*args, **kwargs)
      self.trees = {}
      self.output_view = None
      self.view_name = mlfitype_view_name
      self.type_syntax_file = "Packages/mlfi/mlfi-type.sublime-syntax"
      self.panel_name = mlfitype_panel_name
      self.settings = sublime.load_settings('mlfi.sublime-settings')
      self.single_result = self.settings.get('mlfi_type_single_result', True)

    def run(self, edit):
      queries = []
      
      for r in self.view.sel():
        queries.append(tuple(map(self.__pos_to_point, [r.begin(), r.end()])))

      filename = self.view.file_name()
      if filename == None:
        return

      panel = self.view.window().create_output_panel(self.panel_name)
      buffer = self.__get_mlfi_types_view()

      msg = []
      try:
        (tree, dirty) = self.__get_annot_tree(filename)
        if dirty:
          msg += ["** {0} is newer than its annotation file **".format(os.path.basename(filename))]
        
        # sorting keys
        numlines = lambda itv: itv.end - itv.begin
        # only sort by euclidean distance if we don't use strict range search
        # euc_dist = lambda s, e, i: s.euclidean_dist(i.begin) + e.euclidean_dist(i.end)
        search_point = lambda s, e: sorted(tree[s], key=numlines)
        search_range = lambda s, e: sorted(tree.search(s, e, strict=True), key=lambda i: (i.length(), -i.begin), reverse=True)
        searches = [search_range, search_point]
        results = [(searches[s == e](s,e), s == e) for (s,e) in queries]
        results = [(ts, b) for (ts, b) in results if ts]
        types = [ts[:1] if (b and self.single_result) else ts for (ts, b) in results]

        if any(types):
          tmsg = [self.__mk_msg(ts) for ts in types]
          tmsg = filter(None, tmsg)
          msg += [("\n"*2+"-"*80+"\n"*2).join(tmsg)]
          fts = next(ts for ts in types if ts)
          r = self.__interval_to_region(fts[0])
          self.view.sel().clear()
          self.view.sel().add(r)
          self.view.show(r.begin())
          # self.view.add_regions("omlfi_type", [r], self.view.scope_name(r.begin()), "dot", sublime.DRAW_SQUIGGLY_UNDERLINE)
        else:
          msg += ["No type information found."]
        
      except:
        # msg += [repr(e)]
        msg += [print_exc()]

      finally:  
        self.__append(panel,("\n"*2).join(msg))
        self.__append(buffer,("\n"*2).join(msg))
        panel.set_name(filename)
        self.view.window().run_command('show_panel', { 'panel': 'output.' + self.panel_name })

    def __interval_to_region(self, itv):
      start = self.view.text_point(itv.begin.x-1, itv.begin.y)
      end = self.view.text_point(itv.end.x-1, itv.end.y)
      return sublime.Region(start, end)

    def __interval_to_msg(self, itv):
      r = self.__interval_to_region(itv)
      expr = self.view.substr(r)
      row, col = self.view.rowcol(r.begin())
      return "{0}\n{2}:{3} --> {1}".format(itv.data, expr, row + 1, col + 1)

    def __mk_msg(self, types):
      return "\n\n".join([self.__interval_to_msg(itv) for itv in types])

    def __pos_to_point(self, pos):
        (r, c) = self.view.rowcol(pos)
        return Point(r+1, c)

    def __get_mt(self, filename):
      return os.path.getmtime(filename)

    def __get_annot_tree(self, filename):
      if not os.path.isfile(filename):
        raise ValueError("{0} not found.".format(filename))

      tag = os.path.splitext(filename)[0]
      annot_file = tag + ".annot"

      if not os.path.isfile(annot_file):
        raise ValueError("{0} not found.".format(annot_file))
      
      [fmt, amt] = map(self.__get_mt, [filename, annot_file])
      (tree, dirty) = (None, fmt > amt)

      # if we have a tree already
      if tag in self.trees:
        (tree, mt) = self.trees[tag]
        if mt >= amt:
          return (tree, fmt > mt)
      # make a new tree
      annot = self.__read_file(annot_file)
      
      if annot == None:
        raise ValueError("Cannot read annotation file: {0}.".format(annot_file))

      tree = intervaltree.IntervalTree() 
      af = annot_parser.parse(annot, annot_file, debuglevel=0)
      for b in af.blocks:
        start = Point(b.start.line, b.start.column)
        end = Point(b.end.line, b.end.column)
        data = "\n".join([a.data for a in b.annotations if a.type == "type"])
        if data:
          tree[start:end] = data
      if tree:
        self.trees[tag] = (tree, amt)
      return (tree, dirty)

    def __read_file(self, filename):
      content = None
      f = None
      try:
        f = open(filename, 'r')
        content = f.read()
      except:
        print("Cannot read annotation file: {0}".format(filename))
      finally:
        if f:
          f.close()
      return content

    def __append(self, view, text):
      view.set_syntax_file(self.type_syntax_file)
      view.set_read_only(False)
      if (int(sublime.version()) > 3000):
          view.run_command("select_all")
          view.run_command("right_delete")
          view.run_command('append', {'characters': text})
      else:
          edit = view.begin_edit()
          view.erase(edit, sublime.Region(0, view.size()))
          view.insert(edit, 0, text)
          view.end_edit(edit)
      view.set_read_only(True)

    def __get_mlfi_types_view(self):
      wd = sublime.active_window()
      vs = [v for v in wd.views() if v.name() == self.view_name]
      if any(vs):
        return vs[0]
      av = wd.active_view()
      v = wd.new_file()
      wd.focus_view(av)
      v.set_name(self.view_name)
      v.set_scratch(True)
      return v

class MlfiTypeNextType(sublime_plugin.TextCommand):
    def run(self, edit, forward = True, focus_code = False):
      window = self.view.window()
      panel = window.find_output_panel(mlfitype_panel_name)
      if not panel:
        return
      if window.active_panel() != mlfitype_panel_name:
        window.run_command('show_panel', { 'panel': 'output.' + mlfitype_panel_name })
      code_view = window.find_open_file(panel.name())
      if not code_view:
        return
      caret = panel.sel()[0]
      locs = panel.find_all(r"^[^-*\n](.|\n)*?\d+:\d+\s*-->\s*(.|\n)*?(?=\n^\n|\Z)")
      if not locs:
        return

      if caret.empty() and caret.begin() == 0:
        caret = locs[0]
      if forward:
          mloc = next((l for l in locs if caret.begin() < l.begin()), locs[0])
      else:
          locs.reverse()
          mloc = next((l for l in locs if caret.begin() > l.begin()), locs[0])
          
      if not mloc:
        return
      str = panel.substr(mloc)
      match = re.match(r"^(?P<type>(.|\n)*?)(?P<row>\d+):(?P<col>\d+)\s*-->\s*(?P<expr>(.|\n)*)", str)
      if not match:
        return

      # adjusting the panel and type buffer
      t = match.group('type').strip()
      tr = sublime.Region(mloc.begin(), mloc.begin() + len(t))
      self.__change_viewpoint(panel, tr)
      buffers = [v for v in window.views() if v.name() == "** mlfi types **"]
      [self.__change_viewpoint(b, tr) for b in buffers]

      # change the view
      cord = [int(match.group(v)) for v in ["row", "col"]] 
      b = code_view.text_point(*cord)
      e = b + len(match.group('expr'))
      region = sublime.Region(b,e)
      if focus_code:
        window.focus_view(code_view)
      self.__move_sel_to_region(code_view, region)

    def __move_sel_to_region(self, view, region):
      view.sel().clear()
      view.sel().add(region)
      view.show(region.begin())
      self.__refresh_selection(view)

    def __refresh_selection(self, view):
      # borrowed from https://github.com/SublimeTextIssues/Core/issues/485
      empty_list = []
      bug_reg_key = "selection_bug_demo_workaround_regions_key"
      view.add_regions(bug_reg_key, empty_list,
                            "no_scope", "", sublime.HIDDEN)
      view.erase_regions(bug_reg_key)

    def __change_viewpoint(self, view , region):
      view.sel().clear()
      view.sel().add(region)
      top_offset = view.text_to_layout(region.begin())[1] - view.line_height()
      view.set_viewport_position((0, top_offset), False)