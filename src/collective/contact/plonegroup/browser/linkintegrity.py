from collective.contact.plonegroup.subscribers import search_value_in_objects
from plone.app.linkintegrity.browser.info import DeleteConfirmationInfo
from plone.uuid.interfaces import IUUID


class PlonegroupDeleteConfirmationInfo(DeleteConfirmationInfo):
    """We need to override plone.app.linkintegrity delete confirmation view
    because the breach logic is done in real time and not stored anymore.
    So we cannot just add breaches like we used to do.
    """

    def check_object(self, obj, excluded_path=None, excluded_paths=None):
        """Check one object for breaches.
        Breaches originating from excluded_paths are ignored.
        """
        breaches = super(PlonegroupDeleteConfirmationInfo, self).check_object(
            obj, excluded_path=excluded_path, excluded_paths=excluded_paths
        )
        plonegroup_breaches = search_value_in_objects(
            obj, obj.UID(), p_types=[], type_fields={}
        )
        if not any([breaches, plonegroup_breaches]):
            return

        if breaches is None:
            breaches = {"sources": []}

        for ref_obj in plonegroup_breaches:
            breaches["sources"].append(
                {
                    "uid": IUUID(ref_obj),
                    "title": ref_obj.Title(),
                    "url": ref_obj.absolute_url(),
                    "accessible": self.is_accessible(ref_obj),
                }
            )

        if "target" not in breaches:
            breaches["target"] = {
                "uid": IUUID(obj),
                "title": obj.Title(),
                "url": obj.absolute_url(),
                "portal_type": obj.portal_type,
                "type_title": self.get_portal_type_title(obj),
            }

        return breaches
