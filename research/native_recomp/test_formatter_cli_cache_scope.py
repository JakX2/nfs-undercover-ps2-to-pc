"""Source-only check that fixture CLI planning and analyzer scope share a cache."""
import ast,unittest
from pathlib import Path
HERE=Path(__file__).parent
FILES=["prepare_post_stm_sc_report_formatter_fixture.py","prepare_post_stm_sc_formatter_leaf_fixture.py","prepare_post_stm_sc_report_helper_resume_fixture.py","prepare_post_stm_sc_report_dependency_fixture.py","prepare_formatter_continuation_fixture.py","prepare_formatter_nested_fixture.py"]
class Tests(unittest.TestCase):
    def test_scopes(self):
        for name in FILES:
            with self.subTest(name=name):
                root=ast.parse((HERE/name).read_text())
                main=next(n for n in root.body if isinstance(n,ast.FunctionDef) and n.name=='main')
                scopes=[n for n in ast.walk(main) if isinstance(n,ast.With) and any(isinstance(i.context_expr,ast.Call) and isinstance(i.context_expr.func,ast.Name) and i.context_expr.func.id=='plan_cache_scope' for i in n.items)]
                self.assertEqual(len(scopes),1)
                calls={n.func.id for n in ast.walk(scopes[0]) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
                self.assertTrue({'plan','scope','extend','install'}<=calls)
if __name__=='__main__':unittest.main(verbosity=2)
