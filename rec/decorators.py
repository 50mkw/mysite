def register(*models, site=None):
    """
    Register the given model(s) classes and wrapped ModelRec class with
    rec site:

    @register(Author)
    class AuthorRec(rec.ModelRec):
        pass

    The `site` kwarg is an rec site to use instead of the default rec site.
    """
    from rec import ModelRec
    from rec.sites import site as default_site, RecSite

    def _model_rec_wrapper(rec_class):
        if not models:
            raise ValueError('At least one model must be passed to register.')

        rec_site = site or default_site

        if not isinstance(rec_site, RecSite):
            raise ValueError('site must subclass RecSite')

        if not issubclass(rec_class, ModelRec):
            raise ValueError('Wrapped class must subclass ModelRec.')

        rec_site.register(models, rec_class=rec_class)

        return rec_class
    return _model_rec_wrapper
